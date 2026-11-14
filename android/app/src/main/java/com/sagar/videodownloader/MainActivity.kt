package com.sagar.videodownloader

import android.Manifest
import android.app.Dialog
import android.content.ClipboardManager
import android.content.ContentValues
import android.content.Intent
import android.content.pm.PackageManager
import android.content.res.ColorStateList
import android.graphics.BitmapFactory
import android.graphics.Color
import android.media.MediaScannerConnection
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.provider.MediaStore
import android.view.Gravity
import android.view.View
import android.view.WindowManager
import android.view.inputmethod.EditorInfo
import android.view.inputmethod.InputMethodManager
import android.webkit.MimeTypeMap
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import androidx.core.view.ViewCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.isVisible
import androidx.core.widget.doAfterTextChanged
import androidx.lifecycle.lifecycleScope
import com.sagar.videodownloader.databinding.ActivityMainBinding
import com.yausername.youtubedl_android.YoutubeDL
import com.yausername.youtubedl_android.YoutubeDLRequest
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.async
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import java.util.UUID

class MainActivity : AppCompatActivity() {

    private lateinit var b: ActivityMainBinding
    private lateinit var prefs: Prefs
    private val app get() = application as App

    private var downloadJob: Job? = null
    private var processId: String? = null
    private var savedUri: Uri? = null
    private var savedMime: String = "video/*"
    private var quality = "best"

    private var introDone = false
    private var activeDialog: Dialog? = null
    private var logoTaps = 0
    private var lastTapAt = 0L

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        WindowCompat.setDecorFitsSystemWindows(window, false)
        b = ActivityMainBinding.inflate(layoutInflater)
        setContentView(b.root)
        prefs = Prefs(this)

        applyInsets()
        setupLook()
        setupPlatforms()
        setupActions()
        watchEngine()
        playIntro()

        handleShareIntent(intent)
    }

    override fun onResume() {
        super.onResume()
        if (introDone) checkRemote()
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        handleShareIntent(intent)
    }

    // ================= Look & feel =================

    private fun applyInsets() {
        val c = b.content
        val baseTop = c.paddingTop
        val baseBottom = c.paddingBottom
        ViewCompat.setOnApplyWindowInsetsListener(b.root) { _, insets ->
            val bars = insets.getInsets(WindowInsetsCompat.Type.systemBars() or WindowInsetsCompat.Type.ime())
            c.setPadding(c.paddingLeft, baseTop + bars.top, c.paddingRight, baseBottom + bars.bottom)
            insets
        }
    }

    private fun setupLook() {
        val violet = getColor(R.color.violet)
        val pink = getColor(R.color.pink)
        val amber = getColor(R.color.amber)

        Fx.float(b.blob1, Fx.dp(b.root, 40), Fx.dp(b.root, 60), 9000)
        Fx.float(b.blob2, Fx.dp(b.root, 50), Fx.dp(b.root, 40), 11000)
        Fx.float(b.blob3, Fx.dp(b.root, 60), Fx.dp(b.root, 30), 10000)

        Fx.gradientText(b.brand, violet, pink, amber)
        Fx.gradientText(b.hero2, pink, amber)
        Fx.gradientText(b.introTitle, violet, pink, amber)

        Fx.shine(b.searchShine, b.searchBtn, 600)
        Fx.shine(b.downloadShine, b.downloadBtn, 300)
        Fx.pulse(b.proBadge, 1.06f, 1200)
        Fx.pressable(b.pasteBtn, b.searchBtn, b.downloadBtn, b.openBtn, b.shareBtn,
            b.cancelBtn, b.updateBtn, b.maintRetry, b.logo,
            b.qBest, b.q720, b.q480, b.qAudio)

        b.footer.text = "Made with ❤️ by Sagar  •  v${BuildConfig.VERSION_NAME}"
        selectQuality(b.qBest, "best", animate = false)
    }

    private fun setupPlatforms() {
        val list = listOf(
            "YouTube" to "#FF0033", "Instagram" to "#E1306C", "Facebook" to "#1877F2",
            "X / Twitter" to "#FFFFFF", "Reddit" to "#FF4500", "Vimeo" to "#1AB7EA",
            "Pinterest" to "#E60023", "+1000 aur" to "#FCD34D",
        )
        val d = resources.displayMetrics.density
        list.forEach { (name, color) ->
            val pill = LinearLayout(this).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = Gravity.CENTER_VERTICAL
                setBackgroundResource(R.drawable.bg_pill)
                setPadding((12 * d).toInt(), (7 * d).toInt(), (14 * d).toInt(), (7 * d).toInt())
                layoutParams = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT
                ).apply { marginEnd = (8 * d).toInt() }
            }
            val dot = View(this).apply {
                setBackgroundResource(R.drawable.bg_dot)
                backgroundTintList = ColorStateList.valueOf(Color.parseColor(color))
                layoutParams = LinearLayout.LayoutParams((8 * d).toInt(), (8 * d).toInt())
            }
            val tv = TextView(this).apply {
                text = name
                setTextColor(getColor(R.color.text))
                textSize = 12f
                setPadding((7 * d).toInt(), 0, 0, 0)
            }
            pill.addView(dot)
            pill.addView(tv)
            b.platformRow.addView(pill)
        }
    }

    private fun playIntro() {
        // Intro ke time content chhupa rahe
        listOf(b.header, b.hero1, b.hero2, b.platforms, b.linkCard).forEach { it.alpha = 0f }

        b.introLogo.scaleX = 0.2f; b.introLogo.scaleY = 0.2f; b.introLogo.alpha = 0f
        b.introLogo.rotation = -30f
        b.introTitle.alpha = 0f; b.introTitle.translationY = Fx.dp(b.root, 20)
        b.introSub.alpha = 0f
        b.introRing.alpha = 0f

        b.introLogo.animate().scaleX(1f).scaleY(1f).alpha(1f).rotation(0f)
            .setDuration(800).setInterpolator(android.view.animation.OvershootInterpolator(1.8f)).start()
        b.introRing.animate().alpha(1f).setStartDelay(300).setDuration(500).start()
        Fx.pulse(b.introRing, 1.25f, 900)
        Fx.pulse(b.introGlow, 1.2f, 1300)
        b.introTitle.animate().alpha(1f).translationY(0f).setStartDelay(450).setDuration(600).start()
        b.introSub.animate().alpha(1f).setStartDelay(750).setDuration(600).start()

        lifecycleScope.launch {
            delay(1900)
            b.intro.animate().alpha(0f).setDuration(450).withEndAction {
                b.intro.isVisible = false
            }.start()
            listOf(b.header, b.hero1, b.hero2, b.platforms, b.linkCard).forEachIndexed { i, v ->
                v.alpha = 1f
                Fx.enter(v, 120L + i * 90L)
            }
            for (i in 0 until b.platformRow.childCount) Fx.pop(b.platformRow.getChildAt(i), 500L + i * 60L)
            introDone = true
            askNotificationPermission()
            checkRemote()
        }
    }

    private fun watchEngine() {
        Fx.blink(b.engineDot)
        lifecycleScope.launch {
            val ok = app.ready.await()
            b.engineDot.animate().cancel()
            b.engineDot.alpha = 1f
            if (ok) {
                val v = withContext(Dispatchers.IO) {
                    runCatching { YoutubeDL.getInstance().version(app) }.getOrNull()
                }
                b.engineDot.backgroundTintList = ColorStateList.valueOf(getColor(R.color.ok))
                b.engineText.text = "Engine ready" + (v?.let { "  •  $it" } ?: "")
                Fx.pulse(b.engineDot, 1.4f, 900)
            } else {
                b.engineDot.backgroundTintList = ColorStateList.valueOf(getColor(R.color.err))
                b.engineText.text = "Engine start nahi hua: ${app.initError}"
            }
        }
    }

    private fun askNotificationPermission() {
        if (Build.VERSION.SDK_INT >= 33 && !prefs.askedNotifPermission &&
            ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
            != PackageManager.PERMISSION_GRANTED
        ) {
            prefs.askedNotifPermission = true
            requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 7)
        }
    }

    // ================= Owner controls (remote) =================

    private fun checkRemote() {
        lifecycleScope.launch {
            val cfgJob = async { Remote.fetchConfig() }
            val relJob = async { Remote.fetchLatestRelease() }
            val cfg = cfgJob.await()
            val rel = relJob.await()
            if (isFinishing || isDestroyed) return@launch

            // --- Maintenance ---
            if (cfg != null) {
                if (cfg.maintenance && !prefs.isOwner) {
                    showMaintenance(cfg)
                    return@launch
                } else {
                    hideMaintenance()
                }
                b.ownerBanner.isVisible = prefs.isOwner && cfg.maintenance
                b.ownerBanner.text = "🛠 Maintenance ON hai — sabke liye app band hai, sirf aapke (owner) phone pe chal raha hai."
            }

            if (activeDialog?.isShowing == true) return@launch

            // --- Force update ---
            val installed = Remote.installedVersion
            if (cfg != null && rel != null && installed < cfg.minVersion && rel.version > installed) {
                activeDialog = Fx.dialog(
                    this@MainActivity, "🚀", "Update zaroori hai",
                    "App chalane ke liye naya version install karo." +
                        (cfg.updateNote.takeIf { it.isNotBlank() }?.let { "\n\n✨ Naya kya hai:\n$it" } ?: ""),
                    "⬇️  Abhi update karo", { openUrl(rel.apkUrl()) },
                    cancelable = false,
                )
                return@launch
            }

            // --- Normal update banner ---
            if (rel != null && rel.version > installed) {
                b.updateSub.text = "Version 2.0.${rel.version}" +
                    (cfg?.updateNote?.takeIf { it.isNotBlank() }?.let { " • $it" } ?: "")
                b.updateBtn.setOnClickListener { openUrl(rel.apkUrl()) }
                if (!b.updateBanner.isVisible) Fx.enter(b.updateBanner)
            } else {
                b.updateBanner.isVisible = false
            }

            // --- Owner ka message ---
            if (cfg != null && cfg.messageShow && cfg.messageId > prefs.lastSeenMsgId) {
                prefs.lastSeenMsgId = cfg.messageId
                prefs.lastNotifiedMsgId = maxOf(prefs.lastNotifiedMsgId, cfg.messageId)
                activeDialog = Fx.dialog(
                    this@MainActivity, "📢",
                    cfg.messageTitle.ifBlank { "Sagar ki taraf se" },
                    cfg.messageBody,
                    "Theek hai 👍",
                )
            }
        }
    }

    private fun showMaintenance(cfg: AppConfig) {
        b.maintTitle.text = cfg.maintenanceTitle.ifBlank { "App maintenance pe hai" }
        b.maintMsg.text = cfg.maintenanceMessage.ifBlank { "Hum app ko aur behtar bana rahe hain. Thodi der baad try karo 🙏" }
        if (!b.maintenance.isVisible) {
            b.maintenance.alpha = 0f
            b.maintenance.isVisible = true
            b.maintenance.animate().alpha(1f).setDuration(400).start()
            Fx.spin(b.maintIcon, 5000)
        }
        cancelDownload()
    }

    private fun hideMaintenance() {
        if (b.maintenance.isVisible) {
            b.maintenance.animate().alpha(0f).setDuration(300).withEndAction {
                b.maintenance.isVisible = false
                b.maintIcon.animate().cancel()
            }.start()
        }
    }

    private fun openUrl(url: String) {
        try {
            startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
        } catch (_: Exception) {
            Toast.makeText(this, "Browser nahi khula", Toast.LENGTH_SHORT).show()
        }
    }

    /** Logo pe 7 baar jaldi-jaldi tap = Owner Panel */
    private fun onLogoTap() {
        val now = System.currentTimeMillis()
        logoTaps = if (now - lastTapAt < 600) logoTaps + 1 else 1
        lastTapAt = now
        b.logo.animate().rotationBy(360f).setDuration(400).start()
        if (logoTaps in 4..6) {
            Toast.makeText(this, "Owner Panel: ${7 - logoTaps} aur tap", Toast.LENGTH_SHORT).show()
        }
        if (logoTaps >= 7) {
            logoTaps = 0
            Fx.haptic(b.logo, strong = true)
            startActivity(Intent(this, AdminActivity::class.java))
        }
    }

    // ================= Actions =================

    private fun setupActions() {
        b.logo.setOnClickListener { onLogoTap() }
        b.pasteBtn.setOnClickListener { Fx.haptic(it); pasteFromClipboard() }
        b.searchBtn.setOnClickListener { Fx.haptic(it); search() }
        b.urlInput.setOnEditorActionListener { _, actionId, _ ->
            if (actionId == EditorInfo.IME_ACTION_SEARCH) { search(); true } else false
        }
        b.urlInput.doAfterTextChanged { b.clearBtn.isVisible = !it.isNullOrEmpty() }
        b.clearBtn.setOnClickListener { b.urlInput.setText("") }

        b.qBest.setOnClickListener { selectQuality(b.qBest, "best") }
        b.q720.setOnClickListener { selectQuality(b.q720, "720") }
        b.q480.setOnClickListener { selectQuality(b.q480, "480") }
        b.qAudio.setOnClickListener { selectQuality(b.qAudio, "audio") }

        b.downloadBtn.setOnClickListener { Fx.haptic(it); startDownload() }
        b.cancelBtn.setOnClickListener { cancelDownload() }
        b.openBtn.setOnClickListener { openFile() }
        b.shareBtn.setOnClickListener { shareFile() }
        b.maintRetry.setOnClickListener {
            Fx.spin(b.maintIcon, 800)
            checkRemote()
        }
    }

    private fun selectQuality(card: View, q: String, animate: Boolean = true) {
        quality = q
        listOf(b.qBest, b.q720, b.q480, b.qAudio).forEach {
            it.setBackgroundResource(if (it == card) R.drawable.bg_quality_selected else R.drawable.bg_quality)
        }
        if (animate) {
            Fx.haptic(card)
            card.scaleX = 0.92f; card.scaleY = 0.92f
            card.animate().scaleX(1f).scaleY(1f).setDuration(350)
                .setInterpolator(android.view.animation.OvershootInterpolator(3f)).start()
        }
    }

    /** Kisi aur app se "Share" karke link aaya ho to */
    private fun handleShareIntent(intent: Intent?) {
        if (intent?.action != Intent.ACTION_SEND) return
        val text = intent.getStringExtra(Intent.EXTRA_TEXT) ?: return
        val url = extractUrl(text) ?: return
        b.urlInput.setText(url)
        lifecycleScope.launch {
            if (!introDone) delay(2000)
            search()
        }
    }

    private fun extractUrl(text: String): String? =
        Regex("https?://\\S+").find(text)?.value

    private fun pasteFromClipboard() {
        val cm = getSystemService(ClipboardManager::class.java)
        val text = cm?.primaryClip?.getItemAt(0)?.coerceToText(this)?.toString().orEmpty()
        val url = extractUrl(text)
        if (url == null) {
            showMsg("Clipboard me koi link nahi mila. Pehle video ka link copy karo.", error = true)
            Fx.shake(b.linkCard)
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
        b.urlInput.clearFocus()
    }

    private fun setSearching(on: Boolean) {
        b.searchBtn.isEnabled = !on
        b.searchSpinner.isVisible = on
        b.searchIcon.isVisible = !on
        b.searchText.text = if (on) "Dhoondh rahe…" else "Video dhoondo"
    }

    // ================= Search =================

    private fun search() {
        val url = currentUrl() ?: run {
            showMsg("Pehle video ka link daalo.", error = true)
            Fx.shake(b.linkCard)
            return
        }
        if (downloadJob?.isActive == true) return
        hideKeyboard()
        hideMsg()
        setSearching(true)
        b.infoCard.isVisible = false
        Fx.enter(b.skeleton)
        Fx.blink(b.skeleton)

        lifecycleScope.launch {
            try {
                if (!app.ready.await()) throw Exception("Engine start nahi hua: ${app.initError}")
                val info = withContext(Dispatchers.IO) { YoutubeDL.getInstance().getInfo(url) }

                b.title.text = info.title ?: "Video"
                b.meta.text = listOfNotNull(info.uploader).filter { it.isNotBlank() }
                    .joinToString(" • ").ifBlank { "Video mil gaya ✓" }
                b.siteBadge.text = "● " + (info.extractorKey ?: "Video")
                val duration = info.duration.takeIf { it > 0 }?.let { formatDuration(it) }
                b.durationBadge.isVisible = duration != null
                b.durationBadge.text = duration
                b.thumb.setImageDrawable(null)

                resetResultArea()
                b.skeleton.animate().cancel()
                b.skeleton.alpha = 1f
                b.skeleton.isVisible = false
                Fx.enter(b.infoCard)
                b.scroll.postDelayed({ b.scroll.smoothScrollTo(0, b.infoCard.top - 40) }, 250)

                info.thumbnail?.let { loadThumbnail(it) }
            } catch (e: Exception) {
                b.skeleton.animate().cancel()
                b.skeleton.alpha = 1f
                b.skeleton.isVisible = false
                showMsg(cleanError(e), error = true)
                Fx.shake(b.linkCard)
            } finally {
                setSearching(false)
            }
        }
    }

    private fun resetResultArea() {
        b.progressBox.isVisible = false
        b.successBox.isVisible = false
        b.downloadBtn.isVisible = true
        b.downloadBtn.isEnabled = true
        b.downloadBtn.alpha = 1f
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
            if (bmp != null) {
                b.thumb.alpha = 0f
                b.thumb.setImageBitmap(bmp)
                b.thumb.animate().alpha(1f).setDuration(500).start()
            }
        }
    }

    private fun formatDuration(sec: Int): String {
        val h = sec / 3600
        val m = (sec % 3600) / 60
        val s = sec % 60
        return if (h > 0) "%d:%02d:%02d".format(h, m, s) else "%d:%02d".format(m, s)
    }

    // ================= Download =================

    private fun startDownload() {
        val url = currentUrl() ?: return showMsg("Pehle video ka link daalo.", error = true)
        if (downloadJob?.isActive == true) return

        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.Q &&
            ContextCompat.checkSelfPermission(this, Manifest.permission.WRITE_EXTERNAL_STORAGE)
            != PackageManager.PERMISSION_GRANTED
        ) {
            requestPermissions(arrayOf(Manifest.permission.WRITE_EXTERNAL_STORAGE), 1)
            showMsg("Storage permission do, phir dobara Download dabao.", error = true)
            return
        }

        hideMsg()
        b.downloadBtn.isEnabled = false
        b.downloadBtn.animate().alpha(0.4f).setDuration(200).start()
        b.searchBtn.isEnabled = false
        b.successBox.isVisible = false
        b.progress.isIndeterminate = true
        b.percentText.text = "…"
        b.statusText.text = "Shuru ho raha hai…"
        b.speedText.text = ""
        b.cancelBtn.isVisible = true
        Fx.enter(b.progressBox)
        Fx.pulse(b.progressGlow, 1.12f, 1000)
        b.scroll.postDelayed({ b.scroll.smoothScrollTo(0, b.scroll.getChildAt(0).height) }, 300)
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)

        val id = UUID.randomUUID().toString()
        processId = id
        val tempDir = File(cacheDir, "dl/$id").apply { mkdirs() }
        val q = quality

        downloadJob = lifecycleScope.launch {
            try {
                if (!app.ready.await()) throw Exception("Engine start nahi hua: ${app.initError}")

                val request = YoutubeDLRequest(url).apply {
                    addOption("--no-playlist")
                    addOption("--no-mtime")
                    addOption("-o", tempDir.absolutePath + "/%(title).120B.%(ext)s")
                    when (q) {
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
                                "bestvideo[height<=$q][ext=mp4]+bestaudio[ext=m4a]/" +
                                    "bestvideo[height<=$q]+bestaudio/best[height<=$q]/best"
                            )
                            addOption("--merge-output-format", "mp4")
                        }
                    }
                }

                withContext(Dispatchers.IO) {
                    YoutubeDL.getInstance().execute(request, id) { progress, eta, line ->
                        runOnUiThread { onProgress(progress, eta, line) }
                    }
                }

                b.progress.isIndeterminate = true
                b.percentText.text = "💾"
                b.statusText.text = "Gallery me save ho raha hai…"
                b.speedText.text = ""
                b.cancelBtn.isVisible = false

                val (uri, name) = withContext(Dispatchers.IO) {
                    val file = tempDir.listFiles()
                        ?.filter { it.isFile && !it.name.endsWith(".part") && !it.name.endsWith(".ytdl") }
                        ?.maxByOrNull { it.length() }
                        ?: throw Exception("Download hua par file nahi mili.")
                    saveToDownloads(file) to file.name
                }

                savedUri = uri
                prefs.totalDownloads = prefs.totalDownloads + 1
                showSuccess(name)
            } catch (e: YoutubeDL.CanceledException) {
                Fx.exit(b.progressBox)
                showMsg("Download cancel kar diya.", error = true)
            } catch (e: Exception) {
                Fx.exit(b.progressBox)
                if (downloadJob?.isCancelled == true) {
                    showMsg("Download cancel kar diya.", error = true)
                } else {
                    showMsg(cleanError(e), error = true)
                    b.scroll.post { b.scroll.smoothScrollTo(0, b.linkCard.top) }
                }
            } finally {
                tempDir.deleteRecursively()
                processId = null
                b.downloadBtn.isEnabled = true
                b.downloadBtn.animate().alpha(1f).setDuration(200).start()
                b.searchBtn.isEnabled = true
                b.progressGlow.animate().cancel()
                window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
            }
        }
    }

    private fun onProgress(progress: Float, eta: Long, line: String) {
        if (progress < 0f) {
            b.progress.isIndeterminate = true
            b.statusText.text = "Download ho raha hai…"
            return
        }
        if (b.progress.isIndeterminate) b.progress.isIndeterminate = false
        b.progress.setProgressCompat(progress.toInt(), true)
        b.percentText.text = "${progress.toInt()}%"
        if (progress >= 100f) {
            b.statusText.text = "File taiyaar ho rahi hai…"
            b.speedText.text = ""
        } else {
            b.statusText.text = "Download ho raha hai…"
            val speed = Regex("at\\s+([\\d.]+\\s*[KMG]i?B/s)").find(line)?.groupValues?.get(1)
            b.speedText.text = listOfNotNull(
                speed?.let { "⚡ $it" },
                eta.takeIf { it > 0 }?.let { "⏱ ${formatDuration(it.toInt())} bache" }
            ).joinToString("   ")
        }
    }

    private fun showSuccess(name: String) {
        Fx.exit(b.progressBox) {
            b.downloadBtn.isVisible = false
            b.savedText.text = "Downloads/SagarSaver/$name"
            Fx.enter(b.successBox)
            Fx.pop(b.successCircle, 120)
            b.successCheck.rotation = -90f
            b.successCheck.animate().rotation(0f).setStartDelay(250).setDuration(500).start()
            Fx.haptic(b.successCircle, strong = true)
            b.scroll.postDelayed({ b.scroll.smoothScrollTo(0, b.scroll.getChildAt(0).height) }, 200)
        }
    }

    private fun cancelDownload() {
        processId?.let { YoutubeDL.getInstance().destroyProcessById(it) }
        downloadJob?.cancel()
    }

    /** File ko phone ke Downloads/SagarSaver folder me copy karo */
    private fun saveToDownloads(file: File): Uri {
        val ext = file.extension.lowercase()
        val mime = MimeTypeMap.getSingleton().getMimeTypeFromExtension(ext)
            ?: if (ext == "mp3" || ext == "m4a") "audio/*" else "video/*"
        savedMime = mime

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            val values = ContentValues().apply {
                put(MediaStore.Downloads.DISPLAY_NAME, file.name)
                put(MediaStore.Downloads.MIME_TYPE, mime)
                put(MediaStore.Downloads.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS + "/SagarSaver")
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
                "SagarSaver"
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

    private fun shareFile() {
        val uri = savedUri ?: return
        val intent = Intent(Intent.ACTION_SEND)
            .setType(savedMime)
            .putExtra(Intent.EXTRA_STREAM, uri)
            .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        try {
            startActivity(Intent.createChooser(intent, "Share karo"))
        } catch (_: Exception) {
        }
    }

    // ================= Messages =================

    private fun cleanError(e: Exception): String {
        val msg = e.message ?: return "Kuch gadbad ho gayi."
        val errLine = msg.lines().lastOrNull { it.contains("ERROR") } ?: msg.lines().firstOrNull() ?: msg
        val clean = errLine.replace("ERROR: ", "").trim()
        return when {
            clean.contains("Unsupported URL", true) -> "😕 Ye link support nahi hai. Video ka seedha link daalo."
            clean.contains("Unable to download", true) || clean.contains("resolve host", true) ->
                "📶 Internet check karo, phir dobara try karo.\n($clean)"
            clean.contains("Private", true) || clean.contains("login", true) ->
                "🔒 Ye video private hai ya login maangta hai.\n($clean)"
            else -> "⚠️ " + clean.take(400)
        }
    }

    private fun showMsg(text: String, error: Boolean) {
        b.msg.text = text
        b.msg.setBackgroundResource(if (error) R.drawable.bg_msg_err else R.drawable.bg_msg_ok)
        b.msg.setTextColor(getColor(if (error) R.color.err else R.color.ok))
        if (!b.msg.isVisible) Fx.enter(b.msg)
    }

    private fun hideMsg() {
        b.msg.isVisible = false
    }
}
