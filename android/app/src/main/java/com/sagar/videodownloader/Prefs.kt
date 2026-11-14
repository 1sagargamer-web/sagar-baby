package com.sagar.videodownloader

import android.content.Context

/** Phone pe chhoti settings save karne ke liye */
class Prefs(context: Context) {
    private val sp = context.getSharedPreferences("sagar_saver", Context.MODE_PRIVATE)

    var ownerToken: String?
        get() = sp.getString("owner_token", null)
        set(v) = sp.edit().putString("owner_token", v).apply()

    val isOwner: Boolean get() = !ownerToken.isNullOrBlank()

    var lastSeenMsgId: Long
        get() = sp.getLong("last_seen_msg", 0)
        set(v) = sp.edit().putLong("last_seen_msg", v).apply()

    var lastNotifiedMsgId: Long
        get() = sp.getLong("last_notified_msg", 0)
        set(v) = sp.edit().putLong("last_notified_msg", v).apply()

    var lastNotifiedVersion: Int
        get() = sp.getInt("last_notified_version", 0)
        set(v) = sp.edit().putInt("last_notified_version", v).apply()

    var askedNotifPermission: Boolean
        get() = sp.getBoolean("asked_notif", false)
        set(v) = sp.edit().putBoolean("asked_notif", v).apply()

    var totalDownloads: Int
        get() = sp.getInt("total_downloads", 0)
        set(v) = sp.edit().putInt("total_downloads", v).apply()
}
