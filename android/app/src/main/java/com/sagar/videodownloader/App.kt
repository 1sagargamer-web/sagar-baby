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
import kotlinx.coroutines.delay
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
            // Engine turant ready — search/download ke liye update ka wait nahi
            ready.complete(true)

            // yt-dlp ka naya version (sites badalti rehti hain): din me max 1 baar,
            // thodi der baad, aur sirf jab koi download/search na chal raha ho.
            val prefs = Prefs(this@App)
            if (System.currentTimeMillis() - prefs.lastEngineUpdate > 12 * 60 * 60 * 1000L) {
                delay(8_000)
                val w = Engine.lock.writeLock()
                if (w.tryLock()) {
                    try {
                        YoutubeDL.getInstance().updateYoutubeDL(this@App, YoutubeDL.UpdateChannel.NIGHTLY)
                        prefs.lastEngineUpdate = System.currentTimeMillis()
                    } catch (_: Exception) {
                    } finally {
                        w.unlock()
                    }
                }
            }
        }
    }

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
