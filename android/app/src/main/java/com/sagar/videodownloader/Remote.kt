package com.sagar.videodownloader

import android.os.Build
import android.util.Base64
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

/** Owner jo settings GitHub pe save karta hai (config/sagar-saver.json) */
data class AppConfig(
    val maintenance: Boolean = false,
    val maintenanceTitle: String = "",
    val maintenanceMessage: String = "",
    val messageId: Long = 0,
    val messageTitle: String = "",
    val messageBody: String = "",
    val messageShow: Boolean = false,
    val minVersion: Int = 0,
    val updateNote: String = "",
) {
    fun toJson(): JSONObject = JSONObject()
        .put("maintenance", JSONObject()
            .put("enabled", maintenance)
            .put("title", maintenanceTitle)
            .put("message", maintenanceMessage))
        .put("message", JSONObject()
            .put("id", messageId)
            .put("show", messageShow)
            .put("title", messageTitle)
            .put("body", messageBody))
        .put("update", JSONObject()
            .put("minVersion", minVersion)
            .put("note", updateNote))

    companion object {
        fun fromJson(j: JSONObject): AppConfig {
            val m = j.optJSONObject("maintenance") ?: JSONObject()
            val msg = j.optJSONObject("message") ?: JSONObject()
            val u = j.optJSONObject("update") ?: JSONObject()
            return AppConfig(
                maintenance = m.optBoolean("enabled", false),
                maintenanceTitle = m.optString("title", ""),
                maintenanceMessage = m.optString("message", ""),
                messageId = msg.optLong("id", 0),
                messageShow = msg.optBoolean("show", false),
                messageTitle = msg.optString("title", ""),
                messageBody = msg.optString("body", ""),
                minVersion = u.optInt("minVersion", 0),
                updateNote = u.optString("note", ""),
            )
        }
    }
}

data class Release(val version: Int, val tag: String) {
    fun apkUrl(): String {
        val abi = Build.SUPPORTED_ABIS.firstOrNull().orEmpty()
        val file = if (abi.startsWith("arm64") || abi.startsWith("x86_64")) "SagarSaver-arm64.apk"
        else "SagarSaver-arm32.apk"
        return "https://github.com/${BuildConfig.REPO_OWNER}/${BuildConfig.REPO_NAME}/releases/download/$tag/$file"
    }
}

object Remote {
    private val repo = "${BuildConfig.REPO_OWNER}/${BuildConfig.REPO_NAME}"
    private const val UA = "SagarSaver-Android"

    val installedVersion: Int get() = BuildConfig.VERSION_CODE

    private fun open(url: String, token: String? = null, method: String = "GET"): HttpURLConnection {
        val c = URL(url).openConnection() as HttpURLConnection
        c.requestMethod = method
        c.connectTimeout = 12000
        c.readTimeout = 15000
        c.useCaches = false
        c.setRequestProperty("User-Agent", UA)
        c.setRequestProperty("Cache-Control", "no-cache")
        if (token != null) {
            c.setRequestProperty("Authorization", "Bearer $token")
            c.setRequestProperty("Accept", "application/vnd.github+json")
            c.setRequestProperty("X-GitHub-Api-Version", "2022-11-28")
        }
        return c
    }

    private fun HttpURLConnection.body(): String =
        (if (responseCode in 200..299) inputStream else errorStream)?.bufferedReader()?.use { it.readText() }.orEmpty()

    /** Sab users ke liye: owner ki settings padho. null = internet nahi */
    suspend fun fetchConfig(): AppConfig? = withContext(Dispatchers.IO) {
        try {
            val url = "https://raw.githubusercontent.com/$repo/${BuildConfig.CONFIG_BRANCH}/" +
                "${BuildConfig.CONFIG_PATH}?t=${System.currentTimeMillis() / 60000}"
            val c = open(url)
            when (c.responseCode) {
                200 -> AppConfig.fromJson(JSONObject(c.body()))
                404 -> AppConfig()
                else -> null
            }
        } catch (_: Exception) {
            null
        }
    }

    /** GitHub pe sabse naya APK kaunsa hai (tag apk-N) */
    suspend fun fetchLatestRelease(): Release? = withContext(Dispatchers.IO) {
        try {
            val c = open("https://github.com/$repo/releases/latest")
            c.instanceFollowRedirects = false
            val loc = c.getHeaderField("Location").orEmpty()
            c.disconnect()
            val tag = loc.substringAfterLast("/tag/", "")
            val n = tag.removePrefix("apk-").toIntOrNull()
            if (n != null) Release(n, tag) else null
        } catch (_: Exception) {
            null
        }
    }

    // ---------------- Owner (token chahiye) ----------------

    /** Token sahi hai aur repo me likhne ki permission hai? */
    suspend fun verifyToken(token: String): Result<Unit> = withContext(Dispatchers.IO) {
        try {
            val c = open("https://api.github.com/repos/$repo", token)
            val code = c.responseCode
            val body = c.body()
            when {
                code == 401 -> Result.failure(Exception("Token galat hai ya expire ho gaya."))
                code == 404 -> Result.failure(Exception("Is token se repo '$repo' nahi dikh raha. Repository access me sagar-baby select karo."))
                code !in 200..299 -> Result.failure(Exception("GitHub error $code"))
                else -> {
                    val push = JSONObject(body).optJSONObject("permissions")?.optBoolean("push", false)
                    // Fine-grained tokens kabhi-kabhi permissions nahi bhejte, isliye null ko allow karo
                    if (push == false) Result.failure(Exception("Token me 'Contents: Read and write' permission nahi hai."))
                    else Result.success(Unit)
                }
            }
        } catch (e: Exception) {
            Result.failure(Exception("Internet check karo. (${e.message})"))
        }
    }

    /** Config + uska sha (update karne ke liye zaroori) */
    suspend fun readConfigForOwner(token: String): Pair<AppConfig, String?> = withContext(Dispatchers.IO) {
        val c = open(
            "https://api.github.com/repos/$repo/contents/${BuildConfig.CONFIG_PATH}?ref=${BuildConfig.CONFIG_BRANCH}",
            token
        )
        val code = c.responseCode
        val body = c.body()
        when (code) {
            404 -> AppConfig() to null
            in 200..299 -> {
                val j = JSONObject(body)
                val content = String(Base64.decode(j.getString("content"), Base64.DEFAULT))
                AppConfig.fromJson(JSONObject(content)) to j.getString("sha")
            }
            else -> throw Exception("Config padh nahi paaye (GitHub $code)")
        }
    }

    /** Config GitHub pe save karo. Naya sha return karta hai. */
    suspend fun writeConfig(token: String, cfg: AppConfig, sha: String?, message: String): String =
        withContext(Dispatchers.IO) {
            val payload = JSONObject()
                .put("message", message)
                .put("branch", BuildConfig.CONFIG_BRANCH)
                .put("content", Base64.encodeToString(cfg.toJson().toString(2).toByteArray(), Base64.NO_WRAP))
            if (sha != null) payload.put("sha", sha)

            val c = open(
                "https://api.github.com/repos/$repo/contents/${BuildConfig.CONFIG_PATH}",
                token, "PUT"
            )
            c.doOutput = true
            c.setRequestProperty("Content-Type", "application/json")
            c.outputStream.use { it.write(payload.toString().toByteArray()) }
            val code = c.responseCode
            val body = c.body()
            when (code) {
                200, 201 -> JSONObject(body).getJSONObject("content").getString("sha")
                409, 422 -> throw Exception("Config kahin aur se badla gaya. Panel refresh karke dobara try karo.")
                403 -> throw Exception("Token me likhne ki permission nahi hai (Contents: Read and write).")
                else -> throw Exception("Save nahi hua (GitHub $code)")
            }
        }
}
