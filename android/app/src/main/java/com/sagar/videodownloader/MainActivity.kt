package com.sagar.videodownloader

import android.Manifest
import android.app.Dialog
import android.content.ClipboardManager
import android.content.Intent
import android.content.pm.PackageManager
import android.content.res.ColorStateList
import android.graphics.BitmapFactory
import android.graphics.Color
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.view.inputmethod.EditorInfo
import android.view.inputmethod.InputMethodManager
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.core.view.ViewCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.isVisible
import androidx.core.widget.doAfterTextChanged
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import com.sagar.videodownloader.databinding.ActivityMainBinding
import com.yausername.youtubedl_android.YoutubeDL
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.async
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.net.HttpURLConnection
import java.net.URL

class MainActivity : AppCompatActivity() {

    private lateinit var b: ActivityMainBinding
    private lateinit var prefs: Prefs
    private val app get() = application as App

    private var savedUri: Uri? = null
    private var savedMime: String = "video/*"
    private var quality = "best"

    private var introDone = false
    private var activeDialog: Dialog? = null
    private var logoTaps = 0
    private var lastTapAt = 0L
    private var tapToast: Toast? = null

    private var chooserMode = false       // YouTube lambi video: quality poochni hai
    private var currentTitle = ""
    private var shownDoneUri: Uri? = null
    private var countdownJob: Job? = null

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
        observeDownloads()

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
            while (!app.ready.isCompleted) {
                b.engineText.text = if (app.updatingEngine) "Engine update ho raha hai…" else "Engine start ho raha hai…"
                delay(400)
            }
        }
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
            tapToast?.cancel()
            tapToast = Toast.makeText(this, "Owner Panel: ${7 - logoTaps} aur tap", Toast.LENGTH_SHORT)
            tapToast?.show()
        }
        if (logoTaps >= 7) {
            logoTaps = 0
            tapToast?.cancel()
            Fx.haptic(b.logo, strong = true)
            startActivity(Intent(this, AdminActivity::class.java))
        }
    }

    // ================= Actions =================

    private fun setupActions() {
        b.logo.setOnClickListener { onLogoTap() }
        b.pasteBtn.setOnClickListener { Fx.haptic(it); pasteFromClipboard() }
        b.searchBtn.setOnClickListener { Fx.haptic(it); go() }
        b.urlInput.setOnEditorActionListener { _, actionId, _ ->
            if (actionId == EditorInfo.IME_ACTION_SEARCH) { go(); true } else false
        }
        b.urlInput.doAfterTextChanged { b.clearBtn.isVisible = !it.isNullOrEmpty() }
        b.clearBtn.setOnClickListener { b.urlInput.setText("") }

        b.qBest.setOnClickListener { selectQuality(b.qBest, "best") }
        b.q720.setOnClickListener { selectQuality(b.q720, "720") }
        b.q480.setOnClickListener { selectQuality(b.q480, "480") }
        b.qAudio.setOnClickListener { selectQuality(b.qAudio, "audio") }

        b.downloadBtn.setOnClickListener { Fx.haptic(it); startDownload(quality) }
        b.cancelBtn.setOnClickListener { DownloadService.cancel(this) }
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
            go()
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
        go()
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
        if (!on) b.searchText.text = "Video dhoondo"
    }

    private fun isDownloading() = DownloadState.flow.value is Dl.Running

    // ================= Smart flow =================

    /**
     * YouTube ki normal video -> pehle info (duration) lo:
     *     lambi (>60s) = quality poochho, chhoti = seedha download.
     * Baaki sab (Instagram, Facebook, Shorts, ...) -> seedha download.
     */
    private fun go() {
        val url = currentUrl() ?: run {
            showMsg("Pehle video ka link daalo.", error = true)
            Fx.shake(b.linkCard)
            return
        }
        if (isDownloading()) {
            showMsg("Ek download pehle se chal raha hai. Khatam hone do ya Cancel karo.", error = true)
            return
        }
        hideKeyboard()
        hideMsg()
        DownloadState.flow.value = Dl.Idle
        shownDoneUri = null
        if (Engine.needsInfo(url)) fetchInfo(url) else startDirect(url)
    }

    /** Bina info ke seedha download (sabse fast) */
    private fun startDirect(url: String) {
        val (emoji, name) = Engine.platform(url)
        chooserMode = false
        currentTitle = ""
        b.title.text = "$name video"
        b.meta.text = "⚡ Seedha download ho raha hai"
        b.siteBadge.text = "● $name"
        b.durationBadge.isVisible = false
        b.thumb.setImageDrawable(null)
        b.thumbEmoji.text = emoji
        b.thumbEmoji.isVisible = true
        Fx.pulse(b.thumbEmoji, 1.12f, 900)
        resetResultArea(showQuality = false)
        if (!b.infoCard.isVisible) Fx.enter(b.infoCard)
        startDownload("best")
    }

    private fun fetchInfo(url: String) {
        setSearching(true)
        b.infoCard.isVisible = false
        Fx.enter(b.skeleton)
        Fx.blink(b.skeletonBox)

        val engineWarm = app.ready.isCompleted
        val estimate = ((prefs.avgFetchMs + (if (engineWarm) 0 else if (app.updatingEngine) 12000 else 4000)) / 1000)
            .toInt().coerceIn(2, 40)
        startCountdown(estimate)

        lifecycleScope.launch {
            try {
                if (!app.ready.await()) throw Exception("Engine start nahi hua: ${app.initError}")
                val t1 = System.currentTimeMillis()
                val info = withContext(Dispatchers.IO) {
                    Engine.lock.readLock().lock()
                    try {
                        YoutubeDL.getInstance().getInfo(Engine.infoRequest(url))
                    } finally {
                        Engine.lock.readLock().unlock()
                    }
                }
                // Agli baar ke countdown ke liye andaaza sudhaaro
                val took = System.currentTimeMillis() - t1
                prefs.avgFetchMs = (prefs.avgFetchMs * 2 + took) / 3

                currentTitle = info.title ?: ""
                b.title.text = info.title ?: "Video"
                b.meta.text = info.uploader?.takeIf { it.isNotBlank() } ?: "Video mil gaya ✓"
                b.siteBadge.text = "● YouTube"
                val duration = info.duration
                b.durationBadge.isVisible = duration > 0
                b.durationBadge.text = if (duration > 0) formatDuration(duration) else ""
                b.thumb.setImageDrawable(null)
                b.thumbEmoji.isVisible = false

                stopCountdown()
                b.skeletonBox.animate().cancel()
                b.skeletonBox.alpha = 1f
                b.skeleton.isVisible = false

                val isLong = duration <= 0 || duration > 60
                chooserMode = isLong
                resetResultArea(showQuality = isLong)
                Fx.enter(b.infoCard)
                info.thumbnail?.let { loadThumbnail(it) }

                if (isLong) {
                    b.scroll.postDelayed({ b.scroll.smoothScrollTo(0, b.infoCard.top - 40) }, 250)
                } else {
                    b.meta.text = "⚡ Chhoti video — seedha download ho rahi hai"
                    startDownload("best")
                }
            } catch (e: Exception) {
                stopCountdown()
                b.skeletonBox.animate().cancel()
                b.skeletonBox.alpha = 1f
                b.skeleton.isVisible = false
                showMsg(Engine.cleanError(e), error = true)
                Fx.shake(b.linkCard)
            } finally {
                setSearching(false)
            }
        }
    }

    // ================= Countdown =================

    private fun startCountdown(seconds: Int) {
        countdownJob?.cancel()
        countdownJob = lifecycleScope.launch {
            var s = seconds
            while (true) {
                if (s > 0) {
                    b.skeletonCount.text = s.toString()
                    b.skeletonHint.text = "Video dhoondh rahe hain… lagbhag $s sec"
                    b.searchText.text = "Dhoondh rahe… ${s}s"
                } else {
                    b.skeletonCount.text = "⏳"
                    b.skeletonHint.text = "Bas thoda aur…"
                    b.searchText.text = "Bas thoda aur…"
                }
                b.skeletonCount.scaleX = 1.35f; b.skeletonCount.scaleY = 1.35f; b.skeletonCount.alpha = 0.4f
                b.skeletonCount.animate().scaleX(1f).scaleY(1f).alpha(1f).setDuration(450)
                    .setInterpolator(android.view.animation.OvershootInterpolator(2f)).start()
                delay(1000)
                s--
            }
        }
    }

    private fun stopCountdown() {
        countdownJob?.cancel()
        countdownJob = null
    }

    private fun resetResultArea(showQuality: Boolean) {
        b.progressBox.isVisible = false
        b.successBox.isVisible = false
        b.qualityBox.isVisible = showQuality
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

    // ================= Download (background service) =================

    private fun startDownload(q: String) {
        val url = currentUrl() ?: return showMsg("Pehle video ka link daalo.", error = true)
        if (isDownloading()) return

        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.Q &&
            ContextCompat.checkSelfPermission(this, Manifest.permission.WRITE_EXTERNAL_STORAGE)
            != PackageManager.PERMISSION_GRANTED
        ) {
            requestPermissions(arrayOf(Manifest.permission.WRITE_EXTERNAL_STORAGE), 1)
            showMsg("Storage permission do, phir dobara try karo.", error = true)
            return
        }

        hideMsg()
        // Screen turant update ho, service baad me asli progress bhejega
        DownloadState.flow.value = Dl.Running(url, currentTitle, 0, true, "Shuru ho raha hai…", "", 0)
        try {
            DownloadService.start(this, url, q, currentTitle)
        } catch (e: Exception) {
            DownloadState.flow.value = Dl.Failed(url, "Download shuru nahi hua: ${e.message}")
        }
    }

    /** Service se aane wali progress ko screen pe dikhao (app wapas kholne pe bhi) */
    private fun observeDownloads() {
        lifecycleScope.launch {
            repeatOnLifecycle(Lifecycle.State.STARTED) {
                DownloadState.flow.collect { render(it) }
            }
        }
    }

    private fun render(state: Dl) {
        when (state) {
            is Dl.Idle -> Unit

            is Dl.Running -> {
                if (!b.infoCard.isVisible) {
                    // App dobara khola aur download chal raha hai
                    val (emoji, name) = Engine.platform(state.url)
                    if (b.urlInput.text.isNullOrBlank()) b.urlInput.setText(state.url)
                    b.siteBadge.text = "● $name"
                    b.thumbEmoji.text = emoji
                    b.thumbEmoji.isVisible = b.thumb.drawable == null
                    b.durationBadge.isVisible = false
                    b.meta.text = "⬇️ Download chal raha hai"
                    b.successBox.isVisible = false
                    Fx.enter(b.infoCard)
                }
                if (state.title.isNotBlank() && b.title.text != state.title) b.title.text = state.title
                b.qualityBox.isVisible = false
                b.successBox.isVisible = false
                b.searchBtn.isEnabled = false
                if (!b.progressBox.isVisible) {
                    b.cancelBtn.isVisible = true
                    b.bgHint.isVisible = true
                    Fx.enter(b.progressBox)
                    Fx.pulse(b.progressGlow, 1.12f, 1000)
                    b.scroll.postDelayed({ b.scroll.smoothScrollTo(0, b.scroll.getChildAt(0).height) }, 300)
                }
                if (state.indeterminate || state.percent >= 100) {
                    if (!b.progress.isIndeterminate) b.progress.isIndeterminate = true
                    b.percentText.text = if (state.percent >= 100) "💾" else "…"
                } else {
                    if (b.progress.isIndeterminate) b.progress.isIndeterminate = false
                    b.progress.setProgressCompat(state.percent, true)
                    b.percentText.text = "${state.percent}%"
                }
                b.statusText.text = state.status
                b.cancelBtn.isVisible = state.percent < 100
                b.speedText.text = listOfNotNull(
                    state.speed.takeIf { it.isNotBlank() }?.let { "⚡ $it" },
                    state.etaSec.takeIf { it > 0 }?.let { "⏱ ${DownloadService.fmt(it)} me ho jayega" }
                ).joinToString("   ")
            }

            is Dl.Done -> {
                savedUri = state.uri
                savedMime = state.mime
                b.searchBtn.isEnabled = true
                if (shownDoneUri != state.uri) {
                    shownDoneUri = state.uri
                    if (!b.infoCard.isVisible) Fx.enter(b.infoCard)
                    b.qualityBox.isVisible = false
                    if (state.title.isNotBlank()) b.title.text = state.title
                    showSuccess(state.name)
                }
            }

            is Dl.Failed -> {
                b.searchBtn.isEnabled = true
                Fx.exit(b.progressBox) { if (chooserMode) b.qualityBox.isVisible = true }
                showMsg(state.message, error = true)
                b.scroll.post { b.scroll.smoothScrollTo(0, b.linkCard.top) }
                DownloadState.flow.value = Dl.Idle
            }

            is Dl.Cancelled -> {
                b.searchBtn.isEnabled = true
                Fx.exit(b.progressBox) { if (chooserMode) b.qualityBox.isVisible = true }
                showMsg("Download cancel kar diya.", error = true)
                DownloadState.flow.value = Dl.Idle
            }
        }
    }

    private fun showSuccess(name: String) {
        b.progressGlow.animate().cancel()
        Fx.exit(b.progressBox) {
            b.savedText.text = "Downloads/SagarSaver/$name"
            Fx.enter(b.successBox)
            Fx.pop(b.successCircle, 120)
            b.successCheck.rotation = -90f
            b.successCheck.animate().rotation(0f).setStartDelay(250).setDuration(500).start()
            Fx.haptic(b.successCircle, strong = true)
            b.scroll.postDelayed({ b.scroll.smoothScrollTo(0, b.scroll.getChildAt(0).height) }, 200)
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
