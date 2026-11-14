package com.sagar.videodownloader

import android.Manifest
import android.app.Notification
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder
import android.os.PowerManager
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.app.ServiceCompat
import androidx.core.content.ContextCompat
import com.yausername.youtubedl_android.YoutubeDL
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import java.io.File
import java.util.UUID
import kotlin.concurrent.read

/**
 * Background download: app band karne pe bhi chalta rehta hai.
 * Notification me progress + Cancel button dikhta hai.
 */
class DownloadService : Service() {

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private var job: Job? = null
    private var processId: String? = null
    private var wakeLock: PowerManager.WakeLock? = null
    private var lastNotifyAt = 0L

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_CANCEL -> {
                processId?.let { YoutubeDL.getInstance().destroyProcessById(it) }
                job?.cancel()
                if (job == null) stopSelf()
            }
            ACTION_START -> {
                val url = intent.getStringExtra(EXTRA_URL)
                val quality = intent.getStringExtra(EXTRA_QUALITY) ?: "best"
                val title = intent.getStringExtra(EXTRA_TITLE).orEmpty()
                startFg(progressNotification(title.ifBlank { "Video" }, "Shuru ho raha hai…", 0, true, 0))
                if (url == null) {
                    stopSelf()
                } else if (job?.isActive != true) {
                    start(url, quality, title)
                }
            }
            else -> stopSelf()
        }
        return START_NOT_STICKY
    }

    private fun startFg(n: Notification) {
        val type = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q)
            ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC else 0
        ServiceCompat.startForeground(this, NOTIF_PROGRESS, n, type)
    }

    private fun start(url: String, quality: String, initialTitle: String) {
        val id = UUID.randomUUID().toString()
        processId = id
        val tempDir = File(cacheDir, "dl/$id").apply { mkdirs() }
        var title = initialTitle

        job = scope.launch {
            acquireWakeLock()
            DownloadState.flow.value = Dl.Running(url, title, 0, true, "Shuru ho raha hai…", "", 0)
            try {
                val app = application as App
                if (!app.ready.await()) throw Exception("Engine start nahi hua: ${app.initError}")

                val request = Engine.downloadRequest(this@DownloadService, url, quality, tempDir)
                Engine.lock.read {
                    YoutubeDL.getInstance().execute(request, id) { progress, eta, line ->
                        if (title.isBlank()) {
                            Regex("Destination: (.+)").find(line)?.groupValues?.get(1)?.let {
                                title = File(it.trim()).nameWithoutExtension
                            }
                        }
                        onProgress(url, title, progress, eta, line)
                    }
                }

                DownloadState.flow.value = Dl.Running(url, title, 100, true, "Gallery me save ho raha hai…", "", 0)
                notifyProgress(title, "Save ho raha hai…", 100, true, 0, force = true)

                val file = tempDir.listFiles()
                    ?.filter { it.isFile && !it.name.endsWith(".part") && !it.name.endsWith(".ytdl") }
                    ?.maxByOrNull { it.length() }
                    ?: throw Exception("Download hua par file nahi mili.")
                val mime = Engine.mimeOf(file)
                val uri = Engine.saveToDownloads(this@DownloadService, file)

                Prefs(this@DownloadService).let { it.totalDownloads = it.totalDownloads + 1 }
                val name = file.name
                DownloadState.flow.value = Dl.Done(url, title.ifBlank { file.nameWithoutExtension }, name, uri, mime)
                notifyDone(name, uri, mime)
            } catch (e: YoutubeDL.CanceledException) {
                DownloadState.flow.value = Dl.Cancelled(url)
            } catch (e: CancellationException) {
                DownloadState.flow.value = Dl.Cancelled(url)
            } catch (e: Exception) {
                val msg = Engine.cleanError(e)
                DownloadState.flow.value = Dl.Failed(url, msg)
                notifySimple(NOTIF_RESULT, "❌ Download nahi hua", msg, null)
            } finally {
                tempDir.deleteRecursively()
                processId = null
                releaseWakeLock()
                ServiceCompat.stopForeground(this@DownloadService, ServiceCompat.STOP_FOREGROUND_REMOVE)
                stopSelf()
            }
        }
    }

    private fun onProgress(url: String, title: String, progress: Float, eta: Long, line: String) {
        val indeterminate = progress < 0f
        val p = progress.coerceIn(0f, 100f).toInt()
        val speed = Regex("at\\s+([\\d.]+\\s*[KMG]i?B/s)").find(line)?.groupValues?.get(1).orEmpty()
        val status = when {
            indeterminate -> "Download ho raha hai…"
            p >= 100 -> "File taiyaar ho rahi hai…"
            else -> "Download ho raha hai…"
        }
        DownloadState.flow.value = Dl.Running(url, title, p, indeterminate, status, speed, eta.coerceAtLeast(0))
        val text = buildString {
            append(if (indeterminate) "Download ho raha hai…" else "$p%")
            if (speed.isNotBlank()) append("  •  ⚡ $speed")
            if (eta > 0) append("  •  ⏱ ${fmt(eta)} bache")
        }
        notifyProgress(title.ifBlank { "Video" }, text, p, indeterminate, eta)
    }

    // ---------------- Notifications ----------------

    private fun openAppIntent(): PendingIntent = PendingIntent.getActivity(
        this, 0,
        Intent(this, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP),
        PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
    )

    private fun progressNotification(title: String, text: String, p: Int, indeterminate: Boolean, eta: Long): Notification {
        val cancel = PendingIntent.getService(
            this, 1,
            Intent(this, DownloadService::class.java).setAction(ACTION_CANCEL),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )
        return NotificationCompat.Builder(this, App.CHANNEL_DOWNLOADS)
            .setSmallIcon(R.drawable.ic_download)
            .setColor(0xFFEC4899.toInt())
            .setContentTitle("⬇️ $title")
            .setContentText(text)
            .setSubText(if (eta > 0) "${fmt(eta)} bache" else null)
            .setProgress(100, p, indeterminate)
            .setOngoing(true)
            .setOnlyAlertOnce(true)
            .setSilent(true)
            .setContentIntent(openAppIntent())
            .addAction(0, "Cancel", cancel)
            .setForegroundServiceBehavior(NotificationCompat.FOREGROUND_SERVICE_IMMEDIATE)
            .build()
    }

    private fun notifyProgress(title: String, text: String, p: Int, indeterminate: Boolean, eta: Long, force: Boolean = false) {
        val now = System.currentTimeMillis()
        if (!force && now - lastNotifyAt < 700) return
        lastNotifyAt = now
        if (!canNotify()) return
        try {
            NotificationManagerCompat.from(this)
                .notify(NOTIF_PROGRESS, progressNotification(title, text, p, indeterminate, eta))
        } catch (_: SecurityException) {
        }
    }

    private fun notifyDone(name: String, uri: android.net.Uri, mime: String) {
        val view = Intent(Intent.ACTION_VIEW).setDataAndType(uri, mime)
            .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_ACTIVITY_NEW_TASK)
        val pi = PendingIntent.getActivity(
            this, 2, view, PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )
        notifySimple(NOTIF_RESULT, "✅ Download complete!", "$name\nDownloads/SagarSaver me save ho gaya. Tap karke dekho.", pi)
    }

    private fun notifySimple(id: Int, title: String, body: String, pi: PendingIntent?) {
        if (!canNotify()) return
        val n = NotificationCompat.Builder(this, App.CHANNEL_DONE)
            .setSmallIcon(R.drawable.ic_check)
            .setColor(0xFF34D399.toInt())
            .setContentTitle(title)
            .setContentText(body)
            .setStyle(NotificationCompat.BigTextStyle().bigText(body))
            .setAutoCancel(true)
            .setContentIntent(pi ?: openAppIntent())
            .build()
        try {
            NotificationManagerCompat.from(this).notify(id, n)
        } catch (_: SecurityException) {
        }
    }

    private fun canNotify(): Boolean =
        Build.VERSION.SDK_INT < 33 ||
            ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) ==
            PackageManager.PERMISSION_GRANTED

    // ---------------- Wake lock (screen off pe bhi chale) ----------------

    private fun acquireWakeLock() {
        val pm = getSystemService(Context.POWER_SERVICE) as PowerManager
        wakeLock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "SagarSaver:download").apply {
            setReferenceCounted(false)
            acquire(3 * 60 * 60 * 1000L)
        }
    }

    private fun releaseWakeLock() {
        try {
            if (wakeLock?.isHeld == true) wakeLock?.release()
        } catch (_: Exception) {
        }
        wakeLock = null
    }

    override fun onDestroy() {
        processId?.let { YoutubeDL.getInstance().destroyProcessById(it) }
        scope.cancel()
        releaseWakeLock()
        super.onDestroy()
    }

    companion object {
        const val ACTION_START = "com.sagar.videodownloader.START"
        const val ACTION_CANCEL = "com.sagar.videodownloader.CANCEL"
        const val EXTRA_URL = "url"
        const val EXTRA_QUALITY = "quality"
        const val EXTRA_TITLE = "title"
        private const val NOTIF_PROGRESS = 2001
        private const val NOTIF_RESULT = 2002

        fun fmt(sec: Long): String {
            val h = sec / 3600
            val m = (sec % 3600) / 60
            val s = sec % 60
            return if (h > 0) "%d:%02d:%02d".format(h, m, s) else "%d:%02d".format(m, s)
        }

        fun start(ctx: Context, url: String, quality: String, title: String) {
            val i = Intent(ctx, DownloadService::class.java)
                .setAction(ACTION_START)
                .putExtra(EXTRA_URL, url)
                .putExtra(EXTRA_QUALITY, quality)
                .putExtra(EXTRA_TITLE, title)
            ContextCompat.startForegroundService(ctx, i)
        }

        fun cancel(ctx: Context) {
            ctx.startService(Intent(ctx, DownloadService::class.java).setAction(ACTION_CANCEL))
        }
    }
}
