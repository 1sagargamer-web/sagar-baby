package com.sagar.videodownloader

import android.Manifest
import android.content.ClipboardManager
import android.content.ContentValues
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.BitmapFactory
import android.media.MediaScannerConnection
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.provider.MediaStore
import android.view.WindowManager
import android.view.inputmethod.EditorInfo
import android.view.inputmethod.InputMethodManager
import android.webkit.MimeTypeMap
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import androidx.core.view.isVisible
import androidx.lifecycle.lifecycleScope
import com.sagar.videodownloader.databinding.ActivityMainBinding
import com.yausername.youtubedl_android.YoutubeDL
import com.yausername.youtubedl_android.YoutubeDLRequest
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import java.util.UUID

class MainActivity : AppCompatActivity() {

    private lateinit var b: ActivityMainBinding
    private val app get() = application as App

    private var downloadJob: Job? = null
    private var processId: String? = null
    private var savedUri: Uri? = null
    private var savedMime: String = "video/*"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        b = ActivityMainBinding.inflate(layoutInflater)
        setContentView(b.root)

        b.pasteBtn.setOnClickListener { pasteFromClipboard() }
        b.searchBtn.setOnClickListener { search() }
        b.urlInput.setOnEditorActionListener { _, actionId, _ ->
            if (actionId == EditorInfo.IME_ACTION_SEARCH) { search(); true } else false
        }
        b.downloadBtn.setOnClickListener { startDownload() }
        b.cancelBtn.setOnClickListener { cancelDownload() }
        b.openBtn.setOnClickListener { openFile() }

        b.engineText.text = "⏳ Engine taiyaar ho raha hai… (pehli baar thoda time lagta hai)"
        lifecycleScope.launch {
            val ok = app.ready.await()
            b.engineText.text = if (ok) {
                val v = withContext(Dispatchers.IO) {
                    runCatching { YoutubeDL.getInstance().version(app) }.getOrNull()
                }
                "✅ Engine ready" + (v?.let { " • yt-dlp $it" } ?: "")
            } else {
                "❌ Engine start nahi hua: ${app.initError}"
            }
        }

        handleShareIntent(intent)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        handleShareIntent(intent)
    }

    /** Kisi aur app se "Share" karke link aaya ho to */
    private fun handleShareIntent(intent: Intent?) {
        if (intent?.action != Intent.ACTION_SEND) return
        val text = intent.getStringExtra(Intent.EXTRA_TEXT) ?: return
        val url = extractUrl(text) ?: return
        b.urlInput.setText(url)
        search()
    }

    private fun extractUrl(text: String): String? =
        Regex("https?://\\S+").find(text)?.value

    private fun pasteFromClipboard() {
        val cm = getSystemService(ClipboardManager::class.java)
        val text = cm?.primaryClip?.getItemAt(0)?.coerceToText(this)?.toString().orEmpty()
        val url = extractUrl(text)
        if (url == null) {
            showMsg("Clipboard me koi link nahi mila. Pehle video ka link copy karo.", error = true)
            return
        }
        b.urlInput.setText(url)
        search()
    }

    private fun currentUrl(): String? {
        val raw = b.urlInput.text?.toString()?.trim().orEmpty()
        return extractUrl(raw) ?: raw.takeIf { it.isNotEmpty() }
    }

    private fun hideKeyboard() {
        getSystemService(InputMethodManager::class.java)
            ?.hideSoftInputFromWindow(b.urlInput.windowToken, 0)
    }

    // ---------------- Search ----------------

    private fun search() {
        val url = currentUrl() ?: return showMsg("Pehle video ka link daalo.", error = true)
        if (downloadJob?.isActive == true) return
        hideKeyboard()
        hideMsg()
        b.infoCard.isVisible = false
        b.searchBtn.isEnabled = false
        b.searchBtn.text = "Dhoond rahe…"

        lifecycleScope.launch {
            try {
                if (!app.ready.await()) throw Exception("Engine start nahi hua: ${app.initError}")
                val info = withContext(Dispatchers.IO) { YoutubeDL.getInstance().getInfo(url) }

                b.title.text = info.title ?: "Video"
                val duration = info.duration.takeIf { it > 0 }?.let { formatDuration(it) }
                b.meta.text = listOfNotNull(info.extractorKey, info.uploader, duration)
                    .filter { it.isNotBlank() }.joinToString(" • ")
                b.thumb.setImageDrawable(null)
                b.thumb.isVisible = !info.thumbnail.isNullOrBlank()
                b.progressBox.isVisible = false
                b.openBtn.isVisible = false
                b.downloadBtn.isEnabled = true
                b.infoCard.isVisible = true

                info.thumbnail?.let { loadThumbnail(it) }
            } catch (e: Exception) {
                showMsg(cleanError(e), error = true)
            } finally {
                b.searchBtn.isEnabled = true
                b.searchBtn.text = "🔍 Search"
            }
        }
    }

    private fun loadThumbnail(url: String) {
        lifecycleScope.launch {
            val bmp = withContext(Dispatchers.IO) {
                runCatching {
                    val c = URL(url).openConnection() as HttpURLConnection
                    c.connectTimeout = 10000
                    c.readTimeout = 10000
                    c.inputStream.use { BitmapFactory.decodeStream(it) }
                }.getOrNull()
            }
            if (bmp != null) b.thumb.setImageBitmap(bmp)
        }
    }

    private fun formatDuration(sec: Int): String {
        val h = sec / 3600
        val m = (sec % 3600) / 60
        val s = sec % 60
        return if (h > 0) "%d:%02d:%02d".format(h, m, s) else "%d:%02d".format(m, s)
    }

    // ---------------- Download ----------------

    private fun startDownload() {
        val url = currentUrl() ?: return showMsg("Pehle video ka link daalo.", error = true)

        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.Q &&
            ContextCompat.checkSelfPermission(this, Manifest.permission.WRITE_EXTERNAL_STORAGE)
            != PackageManager.PERMISSION_GRANTED
        ) {
            requestPermissions(arrayOf(Manifest.permission.WRITE_EXTERNAL_STORAGE), 1)
            showMsg("Storage permission do, phir dobara Download dabao.", error = true)
            return
        }

        val quality = when (b.qualityGroup.checkedChipId) {
            b.q720.id -> "720"
            b.q480.id -> "480"
            b.qAudio.id -> "audio"
            else -> "best"
        }

        hideMsg()
        b.downloadBtn.isEnabled = false
        b.searchBtn.isEnabled = false
        b.openBtn.isVisible = false
        b.progressBox.isVisible = true
        b.cancelBtn.isVisible = true
        b.progress.isIndeterminate = true
        b.statusText.text = "Shuru ho raha hai…"
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)

        val id = UUID.randomUUID().toString()
        processId = id
        val tempDir = File(cacheDir, "dl/$id").apply { mkdirs() }

        downloadJob = lifecycleScope.launch {
            try {
                if (!app.ready.await()) throw Exception("Engine start nahi hua: ${app.initError}")

                val request = YoutubeDLRequest(url).apply {
                    addOption("--no-playlist")
                    addOption("--no-mtime")
                    addOption("-o", tempDir.absolutePath + "/%(title).120B.%(ext)s")
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

                withContext(Dispatchers.IO) {
                    YoutubeDL.getInstance().execute(request, id) { progress, eta, _ ->
                        runOnUiThread { onProgress(progress, eta) }
                    }
                }

                b.progress.isIndeterminate = true
                b.statusText.text = "Downloads folder me save ho raha hai…"
                b.cancelBtn.isVisible = false

                val (uri, name) = withContext(Dispatchers.IO) {
                    val file = tempDir.listFiles()
                        ?.filter { it.isFile && !it.name.endsWith(".part") && !it.name.endsWith(".ytdl") }
                        ?.maxByOrNull { it.length() }
                        ?: throw Exception("Download hua par file nahi mili.")
                    saveToDownloads(file) to file.name
                }

                savedUri = uri
                b.progress.isIndeterminate = false
                b.progress.setProgressCompat(100, true)
                b.statusText.text = "✅ Ho gaya!"
                b.openBtn.isVisible = true
                showMsg("Save ho gaya: Downloads/VideoDownloader/$name", error = false)
            } catch (e: YoutubeDL.CanceledException) {
                b.progressBox.isVisible = false
                showMsg("Download cancel kar diya.", error = true)
            } catch (e: Exception) {
                if (downloadJob?.isCancelled == true) {
                    b.progressBox.isVisible = false
                    showMsg("Download cancel kar diya.", error = true)
                } else {
                    b.progressBox.isVisible = false
                    showMsg(cleanError(e), error = true)
                }
            } finally {
                tempDir.deleteRecursively()
                processId = null
                b.downloadBtn.isEnabled = true
                b.searchBtn.isEnabled = true
                window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
            }
        }
    }

    private fun onProgress(progress: Float, eta: Long) {
        if (progress < 0f) {
            b.progress.isIndeterminate = true
            b.statusText.text = "Download ho raha hai…"
            return
        }
        if (b.progress.isIndeterminate) b.progress.isIndeterminate = false
        b.progress.setProgressCompat(progress.toInt(), true)
        b.statusText.text = if (progress >= 100f) {
            "File taiyaar ho rahi hai…"
        } else {
            "Download ho raha hai… ${progress.toInt()}%" + if (eta > 0) " • ${eta}s bache" else ""
        }
    }

    private fun cancelDownload() {
        processId?.let { YoutubeDL.getInstance().destroyProcessById(it) }
        downloadJob?.cancel()
    }

    /** File ko phone ke Downloads/VideoDownloader folder me copy karo */
    private fun saveToDownloads(file: File): Uri {
        val ext = file.extension.lowercase()
        val mime = MimeTypeMap.getSingleton().getMimeTypeFromExtension(ext)
            ?: if (ext == "mp3" || ext == "m4a") "audio/*" else "video/*"
        savedMime = mime

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            val values = ContentValues().apply {
                put(MediaStore.Downloads.DISPLAY_NAME, file.name)
                put(MediaStore.Downloads.MIME_TYPE, mime)
                put(MediaStore.Downloads.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS + "/VideoDownloader")
                put(MediaStore.Downloads.IS_PENDING, 1)
            }
            val resolver = contentResolver
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
                "VideoDownloader"
            ).apply { mkdirs() }
            var dest = File(dir, file.name)
            var n = 1
            while (dest.exists()) {
                dest = File(dir, "${file.nameWithoutExtension} ($n).${file.extension}")
                n++
            }
            file.copyTo(dest)
            MediaScannerConnection.scanFile(this, arrayOf(dest.absolutePath), arrayOf(mime), null)
            return FileProvider.getUriForFile(this, "$packageName.fileprovider", dest)
        }
    }

    private fun openFile() {
        val uri = savedUri ?: return
        val intent = Intent(Intent.ACTION_VIEW)
            .setDataAndType(uri, savedMime)
            .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        try {
            startActivity(Intent.createChooser(intent, "Kis app se kholein?"))
        } catch (e: Exception) {
            Toast.makeText(this, "Koi video player app nahi mila.", Toast.LENGTH_SHORT).show()
        }
    }

    // ---------------- Messages ----------------

    private fun cleanError(e: Exception): String {
        val msg = e.message ?: return "Kuch gadbad ho gayi."
        val errLine = msg.lines().lastOrNull { it.contains("ERROR") } ?: msg.lines().firstOrNull() ?: msg
        val clean = errLine.replace("ERROR: ", "").trim()
        return when {
            clean.contains("Unsupported URL", true) -> "Ye link support nahi hai. Video ka seedha link daalo."
            clean.contains("Unable to download", true) || clean.contains("resolve host", true) ->
                "Internet check karo, phir dobara try karo.\n($clean)"
            clean.contains("Private video", true) || clean.contains("login", true) ->
                "Ye video private hai ya login maangta hai.\n($clean)"
            else -> clean.take(400)
        }
    }

    private fun showMsg(text: String, error: Boolean) {
        b.msg.text = text
        b.msg.setBackgroundResource(if (error) R.drawable.bg_msg_err else R.drawable.bg_msg_ok)
        b.msg.setTextColor(getColor(if (error) R.color.err else R.color.ok))
        b.msg.isVisible = true
    }

    private fun hideMsg() {
        b.msg.isVisible = false
    }
}
