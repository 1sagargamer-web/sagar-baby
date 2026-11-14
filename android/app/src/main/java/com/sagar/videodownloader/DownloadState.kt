package com.sagar.videodownloader

import android.net.Uri
import kotlinx.coroutines.flow.MutableStateFlow

/** Download ki halat — service likhta hai, screen padhti hai */
sealed class Dl {
    data object Idle : Dl()
    data class Running(
        val url: String,
        val title: String,
        val percent: Int,
        val indeterminate: Boolean,
        val status: String,
        val speed: String,
        val etaSec: Long,
    ) : Dl()
    data class Done(val url: String, val title: String, val name: String, val uri: Uri, val mime: String) : Dl()
    data class Failed(val url: String, val message: String) : Dl()
    data class Cancelled(val url: String) : Dl()
}

object DownloadState {
    val flow = MutableStateFlow<Dl>(Dl.Idle)

    /** Jo video download ho rahi hai uski photo (local file path) */
    val thumb = MutableStateFlow<String?>(null)
}
