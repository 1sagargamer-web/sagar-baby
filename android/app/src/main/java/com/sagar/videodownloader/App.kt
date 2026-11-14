package com.sagar.videodownloader

import android.app.Application
import com.yausername.ffmpeg.FFmpeg
import com.yausername.youtubedl_android.YoutubeDL
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

class App : Application() {

    /** true = engine taiyaar, false = init fail hua */
    val ready = CompletableDeferred<Boolean>()
    var initError: String? = null

    override fun onCreate() {
        super.onCreate()
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
}
