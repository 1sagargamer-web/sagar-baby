package com.sagar.videodownloader

import android.content.ContentValues
import android.content.Context
import android.media.MediaScannerConnection
import android.net.Uri
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import android.webkit.MimeTypeMap
import androidx.core.content.FileProvider
import com.yausername.youtubedl_android.YoutubeDLRequest
import java.io.File
import java.util.concurrent.locks.ReentrantReadWriteLock

/** yt-dlp se jude common kaam */
object Engine {

    /**
     * Download/search "read" lock lete hain, engine update "write" lock.
     * Isse update kabhi chalte hue download ko nahi todta.
     */
    val lock = ReentrantReadWriteLock()

    fun isYouTube(url: String) = Regex("(?i)(youtube\\.com|youtu\\.be)").containsMatchIn(url)
    fun isShorts(url: String) = url.contains("/shorts/", ignoreCase = true)

    /** Sirf YouTube ki normal (non-shorts) video pe quality poochni hai */
    fun needsInfo(url: String) = isYouTube(url) && !isShorts(url)

    fun platform(url: String): Pair<String, String> {
        val u = url.lowercase()
        return when {
            "youtu" in u -> "▶️" to "YouTube"
            "instagram" in u -> "📸" to "Instagram"
            "facebook" in u || "fb.watch" in u || "fb.com" in u -> "📘" to "Facebook"
            "twitter" in u || "x.com" in u -> "🐦" to "X / Twitter"
            "reddit" in u -> "👽" to "Reddit"
            "pinterest" in u || "pin.it" in u -> "📌" to "Pinterest"
            "vimeo" in u -> "🎞️" to "Vimeo"
            "snapchat" in u -> "👻" to "Snapchat"
            "threads" in u -> "🧵" to "Threads"
            else -> "🎬" to "Video"
        }
    }

    fun infoRequest(url: String) = YoutubeDLRequest(url).apply {
        addOption("--no-playlist")
        addOption("--no-warnings")
        addOption("--socket-timeout", "15")
        // Sirf title/duration chahiye, saare formats ki list nahi -> jaldi hota hai
        addOption("--extractor-args", "youtube:skip=hls,dash,translated_subs")
    }

    fun downloadRequest(url: String, quality: String, dir: File) = YoutubeDLRequest(url).apply {
        addOption("--no-playlist")
        addOption("--no-mtime")
        addOption("--no-warnings")
        addOption("--socket-timeout", "20")
        addOption("--retries", "5")
        addOption("--fragment-retries", "5")
        addOption("--concurrent-fragments", "4")
        addOption("-o", dir.absolutePath + "/%(title).120B.%(ext)s")
        when (quality) {
            "audio" -> {
                addOption("-f", "bestaudio/best")
                addOption("-x")
                addOption("--audio-format", "mp3")
                addOption("--audio-quality", "192K")
            }
            "best" -> {
                addOption("-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best")
                addOption("--merge-output-format", "mp4")
            }
            else -> {
                addOption(
                    "-f",
                    "bestvideo[height<=$quality][ext=mp4]+bestaudio[ext=m4a]/" +
                        "bestvideo[height<=$quality]+bestaudio/best[height<=$quality]/best"
                )
                addOption("--merge-output-format", "mp4")
            }
        }
    }

    fun mimeOf(file: File): String {
        val ext = file.extension.lowercase()
        return MimeTypeMap.getSingleton().getMimeTypeFromExtension(ext)
            ?: if (ext == "mp3" || ext == "m4a") "audio/*" else "video/*"
    }

    /** File ko phone ke Downloads/SagarSaver folder me copy karo */
    fun saveToDownloads(ctx: Context, file: File): Uri {
        val mime = mimeOf(file)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            val values = ContentValues().apply {
                put(MediaStore.Downloads.DISPLAY_NAME, file.name)
                put(MediaStore.Downloads.MIME_TYPE, mime)
                put(MediaStore.Downloads.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS + "/SagarSaver")
                put(MediaStore.Downloads.IS_PENDING, 1)
            }
            val resolver = ctx.contentResolver
            val uri = resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values)
                ?: throw Exception("Downloads folder me file nahi bana paaye.")
            resolver.openOutputStream(uri)?.use { out -> file.inputStream().use { it.copyTo(out) } }
                ?: throw Exception("Downloads folder me likh nahi paaye.")
            values.clear()
            values.put(MediaStore.Downloads.IS_PENDING, 0)
            resolver.update(uri, values, null, null)
            return uri
        } else {
            @Suppress("DEPRECATION")
            val dir = File(
                Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS),
                "SagarSaver"
            ).apply { mkdirs() }
            var dest = File(dir, file.name)
            var n = 1
            while (dest.exists()) {
                dest = File(dir, "${file.nameWithoutExtension} ($n).${file.extension}")
                n++
            }
            file.copyTo(dest)
            MediaScannerConnection.scanFile(ctx, arrayOf(dest.absolutePath), arrayOf(mime), null)
            return FileProvider.getUriForFile(ctx, "${ctx.packageName}.fileprovider", dest)
        }
    }

    /** Aisa error jo aksar purane yt-dlp ki wajah se aata hai */
    fun looksOutdated(message: String): Boolean {
        val m = message.lowercase()
        return listOf(
            "login required", "rate-limit", "unable to extract", "no video formats",
            "http error 403", "http error 400", "not available", "requested format",
            "unable to download json", "unsupported url",
        ).any { it in m }
    }

    fun cleanError(e: Throwable): String {
        val msg = e.message ?: return "Kuch gadbad ho gayi."
        val errLine = msg.lines().lastOrNull { it.contains("ERROR") } ?: msg.lines().firstOrNull() ?: msg
        val clean = errLine.replace("ERROR: ", "").trim()
        return when {
            clean.contains("Unsupported URL", true) -> "😕 Ye link support nahi hai. Video ka seedha link daalo."
            clean.contains("Unable to download", true) || clean.contains("resolve host", true) ||
                clean.contains("timed out", true) ->
                "📶 Internet check karo, phir dobara try karo.\n($clean)"
            clean.contains("Private", true) || clean.contains("login", true) ->
                "🔒 Ye video private hai ya login maangta hai.\n($clean)"
            else -> "⚠️ " + clean.take(400)
        }
    }
}
