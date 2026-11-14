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
            // Naye yt-dlp version ke liye check (sites badalti rehti hain).
            // Internet na ho to chupchap skip.
            try {
                YoutubeDL.getInstance().updateYoutubeDL(this@App, YoutubeDL.UpdateChannel.STABLE)
            } catch (_: Exception) {
            }
            ready.complete(true)
        }
    }

    private fun createChannel() {
        val ch = NotificationChannel(CHANNEL_ID, "Sagar Saver updates", NotificationManager.IMPORTANCE_HIGH)
        ch.description = "Owner ke messages aur naye updates"
        getSystemService(NotificationManager::class.java).createNotificationChannel(ch)
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
    }
}
