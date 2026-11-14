package com.sagar.videodownloader

import android.Manifest
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters

/** Background me owner ka naya message / naya APK check karke notification bhejta hai */
class UpdateWorker(ctx: Context, params: WorkerParameters) : CoroutineWorker(ctx, params) {

    override suspend fun doWork(): Result {
        val prefs = Prefs(applicationContext)

        Remote.fetchConfig()?.let { cfg ->
            if (cfg.messageShow && cfg.messageId > prefs.lastNotifiedMsgId && cfg.messageId > prefs.lastSeenMsgId) {
                notify(applicationContext, 1001, "📢 " + cfg.messageTitle.ifBlank { "Sagar Saver" }, cfg.messageBody)
                prefs.lastNotifiedMsgId = cfg.messageId
            }
        }

        Remote.fetchLatestRelease()?.let { rel ->
            if (rel.version > Remote.installedVersion && rel.version > prefs.lastNotifiedVersion) {
                notify(applicationContext, 1002, "🚀 Naya update aaya hai!",
                    "Sagar Saver ka naya version ready hai. Tap karke update karo.")
                prefs.lastNotifiedVersion = rel.version
            }
        }
        return Result.success()
    }

    companion object {
        fun notify(ctx: Context, id: Int, title: String, body: String) {
            if (Build.VERSION.SDK_INT >= 33 &&
                ContextCompat.checkSelfPermission(ctx, Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED
            ) return

            val open = PendingIntent.getActivity(
                ctx, id,
                Intent(ctx, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK),
                PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
            )
            val n = NotificationCompat.Builder(ctx, App.CHANNEL_ID)
                .setSmallIcon(R.drawable.ic_notify)
                .setColor(0xFFEC4899.toInt())
                .setContentTitle(title)
                .setContentText(body)
                .setStyle(NotificationCompat.BigTextStyle().bigText(body))
                .setPriority(NotificationCompat.PRIORITY_HIGH)
                .setAutoCancel(true)
                .setContentIntent(open)
                .build()
            try {
                NotificationManagerCompat.from(ctx).notify(id, n)
            } catch (_: SecurityException) {
            }
        }
    }
}
