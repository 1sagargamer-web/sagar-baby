package com.sagar.videodownloader

import android.annotation.SuppressLint
import android.app.Activity
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.os.Bundle
import android.webkit.CookieManager
import android.webkit.WebChromeClient
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import androidx.activity.OnBackPressedCallback
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.isVisible
import com.sagar.videodownloader.databinding.ActivityLoginBinding

/** Instagram / Facebook me login (sirf ek baar) taaki private/login wale videos bhi download hon */
class LoginActivity : AppCompatActivity() {

    private lateinit var b: ActivityLoginBinding
    private lateinit var site: Cookies.Site
    private var finished = false

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        WindowCompat.setDecorFitsSystemWindows(window, false)
        b = ActivityLoginBinding.inflate(layoutInflater)
        setContentView(b.root)

        ViewCompat.setOnApplyWindowInsetsListener(b.root) { v, insets ->
            val bars = insets.getInsets(WindowInsetsCompat.Type.systemBars() or WindowInsetsCompat.Type.ime())
            v.setPadding(0, bars.top, 0, bars.bottom)
            insets
        }

        site = Cookies.ALL.firstOrNull { it.key == intent.getStringExtra(EXTRA_SITE) } ?: Cookies.INSTAGRAM
        b.loginTitle.text = "${site.emoji} ${site.name} login"

        Fx.pressable(b.closeBtn, b.doneBtn)
        b.closeBtn.setOnClickListener { finish() }
        b.doneBtn.setOnClickListener { complete(manual = true) }

        val cm = CookieManager.getInstance()
        cm.setAcceptCookie(true)
        cm.setAcceptThirdPartyCookies(b.web, true)

        b.web.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            databaseEnabled = true
            loadWithOverviewMode = true
            useWideViewPort = true
            // "wv" hatao, warna kuch sites WebView me login rok deti hain
            userAgentString = userAgentString.replace("; wv", "")
        }
        b.web.webChromeClient = object : WebChromeClient() {
            override fun onProgressChanged(view: WebView?, newProgress: Int) {
                b.pageProgress.isVisible = newProgress < 100
            }
        }
        b.web.webViewClient = object : WebViewClient() {
            override fun onPageStarted(view: WebView?, url: String?, favicon: Bitmap?) {
                b.pageProgress.isVisible = true
            }

            override fun onPageFinished(view: WebView?, url: String?) {
                b.pageProgress.isVisible = false
                CookieManager.getInstance().flush()
                // Login hote hi apne aap wapas
                if (Cookies.isLoggedIn(site) && url != null && !url.contains("/login")) {
                    complete(manual = false)
                }
            }
        }

        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (b.web.canGoBack()) b.web.goBack() else finish()
            }
        })

        b.web.loadUrl(site.loginUrl)
    }

    private fun complete(manual: Boolean) {
        if (finished) return
        if (!Cookies.isLoggedIn(site)) {
            if (manual) Toast.makeText(this, "Pehle ${site.name} me login karo 🙂", Toast.LENGTH_SHORT).show()
            return
        }
        finished = true
        Cookies.export(this)
        Toast.makeText(this, "✅ ${site.name} login ho gaya!", Toast.LENGTH_SHORT).show()
        setResult(Activity.RESULT_OK)
        finish()
    }

    override fun onDestroy() {
        b.web.destroy()
        super.onDestroy()
    }

    companion object {
        const val EXTRA_SITE = "site"
        fun intent(ctx: Context, site: Cookies.Site) =
            Intent(ctx, LoginActivity::class.java).putExtra(EXTRA_SITE, site.key)
    }
}
