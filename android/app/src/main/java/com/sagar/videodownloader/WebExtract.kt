package com.sagar.videodownloader

import android.annotation.SuppressLint
import android.content.Context
import android.webkit.CookieManager
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeoutOrNull
import org.json.JSONArray
import org.json.JSONObject
import org.json.JSONTokener
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import kotlin.coroutines.resume

class WebFail(message: String) : Exception(message)

/**
 * Backup plan jab yt-dlp ko Instagram rok de:
 * phone ke asli browser engine (WebView/Chromium) me post kholo, page me se video ka
 * direct link nikalo aur khud download karo. Login ki zaroorat nahi.
 */
object WebExtract {

    data class Media(val videoUrl: String, val thumbUrl: String?, val title: String)

    private val CODE_RE = Regex("instagram\\.com/(?:[^/?#]+/)?(?:p|reel|reels|tv)/([A-Za-z0-9_-]+)")

    fun shortcode(url: String): String? = CODE_RE.find(url)?.groupValues?.get(1)

    private fun desktopUa(ctx: Context): String {
        val major = Regex("Chrome/(\\d+)").find(WebSettings.getDefaultUserAgent(ctx))?.groupValues?.get(1) ?: "124"
        return "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) " +
            "Chrome/$major.0.0.0 Safari/537.36"
    }

    // Page me jo JSON/meta chahiye wo nikaalne wali JavaScript
    private const val SCRIPT_POST = """
        (function(){
          var out=[], s=document.querySelectorAll('script');
          for(var i=0;i<s.length;i++){
            var t=s[i].textContent||'';
            if(t.indexOf('video_versions')>-1){out.push(t);}
          }
          function m(p){var e=document.querySelector('meta[property="'+p+'"]');return e?(e.content||''):'';}
          return JSON.stringify({scripts:out,ogv:m('og:video'),ogvs:m('og:video:secure_url'),
            ogi:m('og:image'),href:location.href});
        })()
    """

    private const val SCRIPT_EMBED = """
        (function(){
          var v=document.querySelector('video');
          var src=v?(v.currentSrc||v.src||''):'';
          var html=document.documentElement.outerHTML||'';
          var mm=html.match(/"video_url":"([^"]+)"/);
          var im=document.querySelector('img.EmbeddedMediaImage');
          return JSON.stringify({src:src,vurl:mm?mm[1]:'',ogi:im?im.src:'',href:location.href,len:html.length});
        })()
    """

    /** Pehle normal post page, na mile to embed page */
    suspend fun instagram(ctx: Context, url: String): Media {
        val code = shortcode(url) ?: throw WebFail("link se post ka code nahi mila")
        val problems = mutableListOf<String>()
        for (mode in listOf("post", "embed")) {
            try {
                return withContext(Dispatchers.Main) { loadAndParse(ctx, code, mode) }
            } catch (e: CancellationException) {
                throw e
            } catch (e: WebFail) {
                problems += "$mode: ${e.message}"
            } catch (e: Exception) {
                problems += "$mode: ${e.javaClass.simpleName}"
            }
        }
        throw WebFail(problems.joinToString(" | "))
    }

    @SuppressLint("SetJavaScriptEnabled")
    private suspend fun loadAndParse(ctx: Context, code: String, mode: String): Media {
        val wv = WebView(ctx.applicationContext)
        try {
            CookieManager.getInstance().apply {
                setAcceptCookie(true)
                removeAllCookies(null)
            }
            wv.settings.apply {
                javaScriptEnabled = true
                domStorageEnabled = true
                userAgentString = desktopUa(ctx)
                blockNetworkImage = true
            }
            val loaded = CompletableDeferred<String>()
            wv.webViewClient = object : WebViewClient() {
                override fun onPageFinished(view: WebView?, url: String?) {
                    loaded.complete(url.orEmpty())
                }

                override fun onReceivedError(view: WebView?, request: WebResourceRequest?, error: WebResourceError?) {
                    if (request?.isForMainFrame == true) loaded.complete("error:" + (error?.description ?: ""))
                }
            }

            val pageUrl = if (mode == "post") "https://www.instagram.com/p/$code/"
            else "https://www.instagram.com/p/$code/embed/captioned/"
            wv.loadUrl(pageUrl)

            val first = withTimeoutOrNull(20_000) { loaded.await() }
                ?: throw WebFail("page load nahi hua (timeout)")
            if (first.startsWith("error:")) throw WebFail("page nahi khula (${first.removePrefix("error:").take(40)})")

            var href = first
            var info = ""
            for (attempt in 0 until 8) {
                delay(if (attempt == 0) 800L else 1000L)
                val json = wv.eval(if (mode == "post") SCRIPT_POST else SCRIPT_EMBED) ?: continue
                val o = runCatching { JSONObject(json) }.getOrNull() ?: continue
                href = o.optString("href", href)
                if (href.contains("/accounts/login")) throw WebFail("Instagram ne login page pe bhej diya")
                val media = if (mode == "post") parsePost(o, code) else parseEmbed(o)
                if (media != null) return media
                info = if (mode == "post") "scripts=${o.optJSONArray("scripts")?.length() ?: 0}"
                else "len=${o.optInt("len")}"
            }
            throw WebFail("video ka data nahi mila ($info)")
        } finally {
            wv.stopLoading()
            wv.destroy()
        }
    }

    private suspend fun WebView.eval(script: String): String? = suspendCancellableCoroutine { c ->
        evaluateJavascript(script) { r ->
            val v = runCatching { JSONTokener(r ?: "null").nextValue() }.getOrNull()
            c.resume(v as? String)
        }
    }

    // ---------- Parsing ----------

    private fun parsePost(o: JSONObject, code: String): Media? {
        val scripts = o.optJSONArray("scripts")
        if (scripts != null) {
            for (i in 0 until scripts.length()) {
                val root = runCatching { JSONTokener(scripts.getString(i)).nextValue() }.getOrNull() ?: continue
                val media = findMedia(root, code) ?: continue
                val vv = media.optJSONArray("video_versions") ?: continue

                var bestUrl: String? = null
                var bestArea = -1L
                for (k in 0 until vv.length()) {
                    val v = vv.optJSONObject(k) ?: continue
                    val u = v.optString("url")
                    if (u.isBlank()) continue
                    val area = v.optLong("width") * v.optLong("height")
                    if (area > bestArea) {
                        bestArea = area
                        bestUrl = u
                    }
                }
                if (bestUrl == null) continue

                val user = media.optJSONObject("user")?.optString("username").orEmpty()
                val caption = media.optJSONObject("caption")?.optString("text").orEmpty()
                    .replace(Regex("\\s+"), " ").trim().take(60)
                val title = listOf("Instagram", user, caption).filter { it.isNotBlank() }.joinToString(" - ")
                val thumb = media.optJSONObject("image_versions2")?.optJSONArray("candidates")
                    ?.optJSONObject(0)?.optString("url")?.takeIf { it.startsWith("http") }
                return Media(bestUrl, thumb, title)
            }
        }
        val og = o.optString("ogvs").ifBlank { o.optString("ogv") }
        if (og.startsWith("http")) {
            return Media(og, o.optString("ogi").takeIf { it.startsWith("http") }, "Instagram video")
        }
        return null
    }

    private fun parseEmbed(o: JSONObject): Media? {
        val src = o.optString("src")
        val vurl = o.optString("vurl")
        val direct = when {
            src.startsWith("http") -> src
            vurl.isNotBlank() -> (runCatching { JSONTokener("\"$vurl\"").nextValue() }.getOrNull() as? String).orEmpty()
            else -> ""
        }
        if (!direct.startsWith("http")) return null
        return Media(direct, o.optString("ogi").takeIf { it.startsWith("http") }, "Instagram video")
    }

    /** JSON me us post ka object dhoondo jisme video_versions ho */
    private fun findMedia(node: Any?, code: String): JSONObject? {
        when (node) {
            is JSONObject -> {
                val vv = node.optJSONArray("video_versions")
                val c = node.optString("code")
                if (vv != null && vv.length() > 0 && (c.isEmpty() || c == code)) return node
                val keys = node.keys()
                while (keys.hasNext()) {
                    findMedia(node.opt(keys.next()), code)?.let { return it }
                }
            }
            is JSONArray -> for (i in 0 until node.length()) {
                findMedia(node.opt(i), code)?.let { return it }
            }
        }
        return null
    }

    // ---------- Download ----------

    /** Seedha link se file download; onProgress(done, total, bytesPerSec) */
    suspend fun download(
        ctx: Context,
        url: String,
        dest: File,
        onProgress: (Long, Long, Long) -> Unit,
    ) {
        withContext(Dispatchers.IO) {
            val c = (URL(url).openConnection() as HttpURLConnection).apply {
                connectTimeout = 15_000
                readTimeout = 30_000
                instanceFollowRedirects = true
                setRequestProperty("User-Agent", desktopUa(ctx))
                setRequestProperty("Referer", "https://www.instagram.com/")
                setRequestProperty("Accept", "*/*")
            }
            try {
                val status = c.responseCode
                if (status !in 200..299) throw WebFail("video link se download nahi hua (HTTP $status)")
                val total = c.contentLengthLong
                c.inputStream.use { input ->
                    dest.outputStream().use { out ->
                        val buf = ByteArray(64 * 1024)
                        var done = 0L
                        val t0 = System.currentTimeMillis()
                        var lastReport = 0L
                        while (true) {
                            val n = input.read(buf)
                            if (n < 0) break
                            out.write(buf, 0, n)
                            done += n
                            ensureActive()
                            val now = System.currentTimeMillis()
                            if (now - lastReport > 400) {
                                lastReport = now
                                val sec = maxOf(1.0, (now - t0) / 1000.0)
                                onProgress(done, total, (done / sec).toLong())
                            }
                        }
                    }
                }
                if (dest.length() == 0L) throw WebFail("khaali file aayi")
            } finally {
                c.disconnect()
            }
        }
    }
}
