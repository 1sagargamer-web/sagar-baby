package com.sagar.videodownloader

import android.content.Context
import android.webkit.CookieManager
import java.io.File

/**
 * Instagram/Facebook login ke cookies ko yt-dlp wali cookies.txt file me badalta hai.
 * Sab kuch sirf phone ke andar rehta hai.
 */
object Cookies {

    data class Site(
        val key: String,
        val name: String,
        val emoji: String,
        val loginUrl: String,
        val cookieUrl: String,
        val domain: String,
        val sessionCookie: String,
    )

    val INSTAGRAM = Site(
        "instagram", "Instagram", "📸",
        "https://www.instagram.com/accounts/login/",
        "https://www.instagram.com", ".instagram.com", "sessionid"
    )
    val FACEBOOK = Site(
        "facebook", "Facebook", "📘",
        "https://m.facebook.com/login/",
        "https://www.facebook.com", ".facebook.com", "c_user"
    )
    val ALL = listOf(INSTAGRAM, FACEBOOK)

    fun forUrl(url: String): Site? {
        val u = url.lowercase()
        return when {
            "instagram" in u -> INSTAGRAM
            "facebook" in u || "fb.watch" in u || "fb.com" in u -> FACEBOOK
            else -> null
        }
    }

    fun file(ctx: Context) = File(ctx.filesDir, "cookies.txt")

    private fun raw(site: Site): String =
        CookieManager.getInstance().getCookie(site.cookieUrl).orEmpty()

    fun isLoggedIn(site: Site): Boolean =
        raw(site).split(";").any { it.trim().startsWith(site.sessionCookie + "=") }

    /** Sab logged-in sites ke cookies cookies.txt me likho */
    fun export(ctx: Context) {
        CookieManager.getInstance().flush()
        val expiry = System.currentTimeMillis() / 1000 + 365L * 24 * 3600
        val sb = StringBuilder("# Netscape HTTP Cookie File\n")
        var any = false
        for (site in ALL) {
            val cookies = raw(site)
            if (cookies.isBlank()) continue
            for (part in cookies.split(";")) {
                val p = part.trim()
                val i = p.indexOf('=')
                if (i <= 0) continue
                val name = p.substring(0, i)
                val value = p.substring(i + 1)
                sb.append(site.domain).append("\tTRUE\t/\tTRUE\t")
                    .append(expiry).append('\t').append(name).append('\t').append(value).append('\n')
                any = true
            }
        }
        val f = file(ctx)
        if (any) f.writeText(sb.toString()) else f.delete()
    }

    fun logoutAll(ctx: Context) {
        CookieManager.getInstance().removeAllCookies(null)
        CookieManager.getInstance().flush()
        file(ctx).delete()
    }

    /** yt-dlp ka error batata hai ki login chahiye */
    fun needsLogin(message: String): Boolean {
        val m = message.lowercase()
        return listOf(
            "login required", "rate-limit", "rate limit", "--cookies", "cookies-from-browser",
            "log in", "logged-in", "login", "not available", "private", "checkpoint",
        ).any { it in m }
    }
}
