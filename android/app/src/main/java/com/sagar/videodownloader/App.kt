package com.sagar.videodownloader

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import androidx.work.Constraints
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.NetworkType
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import com.yausername.ffmpeg.FFmpeg
import com.yausername.youtubedl_android.YoutubeDL
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.launch
import java.util.concurrent.TimeUnit

class App : Application() {

    /** true = engine taiyaar, false = init fail hua */
    val ready = CompletableDeferred<Boolean>()
    var initError: String? = null

    override fun onCreate() {
        super.onCreate()
        createChannel()
        scheduleChecks()

        CoroutineScope(SupervisorJob() + Dispatchers.IO).launch {
            try {
                YoutubeDL.getInstance().init(this@App)
                FFmpeg.getInstance().init(this@App)
            } catch (e: Exception) {
                initError = e.message
                ready.complete(false)
                return@launch
            }
            // Pehle jaisa: engine (yt-dlp) update hone ke baad hi ready.
            // Lekin din me sirf 1 baar — baaki time app turant ready.
            val prefs = Prefs(this@App)
            if (System.currentTimeMillis() - prefs.lastEngineUpdate > 24 * 60 * 60 * 1000L) {
                updatingEngine = true
                try {
                    YoutubeDL.getInstance().updateYoutubeDL(this@App, YoutubeDL.UpdateChannel.STABLE)
                    prefs.lastEngineUpdate = System.currentTimeMillis()
                } catch (_: Exception) {
                }
                updatingEngine = false
            }
            ready.complete(true)
        }
    }

    @Volatile
    var updatingEngine = false

    private val updateMutex = Mutex()

    /**
     * Download fail hua (site ne kuch badla) -> engine abhi update karo.
     * true = naya version aaya, dobara try karne layak.
     */
    suspend fun updateEngineNow(): Boolean = updateMutex.withLock {
        val prefs = Prefs(this)
        if (System.currentTimeMillis() - lastForcedUpdate < 10 * 60 * 1000L) return@withLock false
        lastForcedUpdate = System.currentTimeMillis()
        val w = Engine.lock.writeLock()
        w.lock()
        try {
            val st = YoutubeDL.getInstance().updateYoutubeDL(this, YoutubeDL.UpdateChannel.STABLE)
            prefs.lastEngineUpdate = System.currentTimeMillis()
            st == YoutubeDL.UpdateStatus.DONE
        } catch (_: Exception) {
            false
        } finally {
            w.unlock()
        }
    }

    private var lastForcedUpdate = 0L

    private fun createChannel() {
        val nm = getSystemService(NotificationManager::class.java)
        nm.createNotificationChannel(
            NotificationChannel(CHANNEL_ID, "Messages aur updates", NotificationManager.IMPORTANCE_HIGH)
                .apply { description = "Owner ke messages aur naye updates" }
        )
        nm.createNotificationChannel(
            NotificationChannel(CHANNEL_DOWNLOADS, "Download progress", NotificationManager.IMPORTANCE_LOW)
                .apply { description = "Background me chal raha download"; setShowBadge(false) }
        )
        nm.createNotificationChannel(
            NotificationChannel(CHANNEL_DONE, "Download complete", NotificationManager.IMPORTANCE_DEFAULT)
                .apply { description = "Download poora hone pe" }
        )
    }

    /** Har ~30 minute me owner ka message / naya update check karo */
    private fun scheduleChecks() {
        val req = PeriodicWorkRequestBuilder<UpdateWorker>(30, TimeUnit.MINUTES)
            .setConstraints(Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build())
            .build()
        WorkManager.getInstance(this)
            .enqueueUniquePeriodicWork("sagar_checks", ExistingPeriodicWorkPolicy.KEEP, req)
    }

    companion object {
        const val CHANNEL_ID = "sagar_updates"
        const val CHANNEL_DOWNLOADS = "sagar_downloads"
        const val CHANNEL_DONE = "sagar_done"
    }
}
