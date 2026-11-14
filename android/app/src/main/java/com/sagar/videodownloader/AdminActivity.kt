package com.sagar.videodownloader

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.isVisible
import androidx.lifecycle.lifecycleScope
import com.sagar.videodownloader.databinding.ActivityAdminBinding
import kotlinx.coroutines.launch

/** 👑 Owner Panel: message bhejo, maintenance ON/OFF, force update */
class AdminActivity : AppCompatActivity() {

    private lateinit var b: ActivityAdminBinding
    private lateinit var prefs: Prefs

    private var cfg = AppConfig()
    private var sha: String? = null
    private var latest: Release? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        WindowCompat.setDecorFitsSystemWindows(window, false)
        b = ActivityAdminBinding.inflate(layoutInflater)
        setContentView(b.root)
        prefs = Prefs(this)

        val c = b.content
        val top = c.paddingTop
        val bottom = c.paddingBottom
        ViewCompat.setOnApplyWindowInsetsListener(b.root) { _, insets ->
            val bars = insets.getInsets(WindowInsetsCompat.Type.systemBars() or WindowInsetsCompat.Type.ime())
            c.setPadding(c.paddingLeft, top + bars.top, c.paddingRight, bottom + bars.bottom)
            insets
        }

        Fx.float(b.blob1, Fx.dp(b.root, 40), Fx.dp(b.root, 50), 9000)
        Fx.float(b.blob2, Fx.dp(b.root, 50), Fx.dp(b.root, 40), 11000)
        Fx.pressable(b.backBtn, b.loginBtn, b.sendMsgBtn, b.clearMsgBtn, b.saveMaintBtn,
            b.saveNoteBtn, b.forceUpdateBtn, b.unforceBtn, b.logoutBtn)

        b.backBtn.setOnClickListener { finish() }
        b.loginBtn.setOnClickListener { login() }
        b.sendMsgBtn.setOnClickListener { sendMessage() }
        b.clearMsgBtn.setOnClickListener { clearMessage() }
        b.saveMaintBtn.setOnClickListener { saveMaintenance() }
        b.saveNoteBtn.setOnClickListener { saveNote() }
        b.forceUpdateBtn.setOnClickListener { forceUpdate() }
        b.unforceBtn.setOnClickListener { unforce() }
        b.logoutBtn.setOnClickListener { logout() }

        if (prefs.isOwner) loadPanel() else showLogin()
    }

    // ---------------- Login ----------------

    private fun showLogin() {
        b.panel.isVisible = false
        b.adminSub.text = "Login karke app control karo"
        Fx.enter(b.loginCard)
    }

    private fun login() {
        val token = b.tokenInput.text.toString().trim()
        if (token.length < 20) {
            toast("Sahi GitHub token paste karo.", error = true)
            Fx.shake(b.loginCard)
            return
        }
        busy(true)
        lifecycleScope.launch {
            val r = Remote.verifyToken(token)
            busy(false)
            r.onSuccess {
                prefs.ownerToken = token
                Fx.haptic(b.loginBtn, strong = true)
                b.loginCard.isVisible = false
                toast("Welcome back, Sagar 👑", error = false)
                loadPanel()
            }.onFailure {
                toast(it.message ?: "Login fail", error = true)
                Fx.shake(b.loginCard)
            }
        }
    }

    private fun logout() {
        Fx.dialog(this, "🚪", "Logout karein?",
            "Is phone se owner access hat jayega. Dobara login ke liye token chahiye hoga.",
            "Haan, logout", {
                prefs.ownerToken = null
                b.panel.isVisible = false
                showLogin()
            }, "Rehne do")
    }

    // ---------------- Panel ----------------

    private fun loadPanel() {
        val token = prefs.ownerToken ?: return showLogin()
        b.adminSub.text = "Loading…"
        busy(true)
        lifecycleScope.launch {
            try {
                val (c, s) = Remote.readConfigForOwner(token)
                cfg = c
                sha = s
                latest = Remote.fetchLatestRelease()
                render()
                b.adminSub.text = "Sab kuch aapke control me hai"
                if (!b.panel.isVisible) {
                    b.panel.isVisible = true
                    for (i in 0 until b.panel.childCount) Fx.enter(b.panel.getChildAt(i), i * 80L)
                }
            } catch (e: Exception) {
                b.adminSub.text = "Load nahi hua"
                toast(e.message ?: "Error", error = true)
            } finally {
                busy(false)
            }
        }
    }

    private fun render() {
        val installed = Remote.installedVersion
        b.statInstalled.text = "v$installed"
        b.statLatest.text = latest?.let { "v${it.version}" } ?: "—"
        b.statMaint.text = if (cfg.maintenance) "BAND 🛠" else "LIVE ✓"
        b.statMaint.setTextColor(getColor(if (cfg.maintenance) R.color.err else R.color.ok))

        b.currentMsg.text = if (cfg.messageShow && cfg.messageBody.isNotBlank())
            "Abhi live message: \"${cfg.messageTitle}\" — ${cfg.messageBody.take(80)}"
        else "Abhi koi message live nahi hai."

        b.maintSwitch.isChecked = cfg.maintenance
        if (b.maintTitleInput.text.isNullOrBlank()) b.maintTitleInput.setText(cfg.maintenanceTitle)
        if (b.maintMsgInput.text.isNullOrBlank()) b.maintMsgInput.setText(cfg.maintenanceMessage)
        if (b.updateNoteInput.text.isNullOrBlank()) b.updateNoteInput.setText(cfg.updateNote)

        b.currentForce.text = if (cfg.minVersion > 0)
            "Force update ON: v${cfg.minVersion} se purane version nahi chalenge."
        else "Force update OFF hai."
    }

    /** Config badlo aur GitHub pe save karo */
    private fun save(newCfg: AppConfig, commitMsg: String, successMsg: String) {
        val token = prefs.ownerToken ?: return showLogin()
        busy(true)
        lifecycleScope.launch {
            try {
                // Taaza sha lo, taaki conflict na ho
                val (_, freshSha) = Remote.readConfigForOwner(token)
                sha = Remote.writeConfig(token, newCfg, freshSha, commitMsg)
                cfg = newCfg
                render()
                Fx.haptic(b.root, strong = true)
                Fx.dialog(this@AdminActivity, "✅", "Ho gaya!",
                    "$successMsg\n\nSab users tak pahunchne me 5 minute tak lag sakte hain.",
                    "Badhiya 👍")
            } catch (e: Exception) {
                toast(e.message ?: "Save nahi hua", error = true)
            } finally {
                busy(false)
            }
        }
    }

    private fun sendMessage() {
        val title = b.msgTitle.text.toString().trim()
        val body = b.msgBody.text.toString().trim()
        if (body.isEmpty()) {
            toast("Message khali hai.", error = true)
            Fx.shake(b.msgBody)
            return
        }
        Fx.dialog(this, "📢", "Sabko bhejein?",
            "\"${title.ifBlank { "Sagar ki taraf se" }}\"\n$body",
            "🚀  Haan, bhejo", {
                save(
                    cfg.copy(
                        messageId = System.currentTimeMillis(),
                        messageShow = true,
                        messageTitle = title,
                        messageBody = body,
                    ),
                    "Owner message: ${title.ifBlank { body.take(40) }}",
                    "Message sabko bhej diya gaya."
                )
                b.msgTitle.setText("")
                b.msgBody.setText("")
            }, "Ruko")
    }

    private fun clearMessage() {
        save(cfg.copy(messageShow = false), "Owner message hataya", "Message hata diya gaya.")
    }

    private fun saveMaintenance() {
        val on = b.maintSwitch.isChecked
        save(
            cfg.copy(
                maintenance = on,
                maintenanceTitle = b.maintTitleInput.text.toString().trim(),
                maintenanceMessage = b.maintMsgInput.text.toString().trim(),
            ),
            if (on) "Maintenance ON" else "Maintenance OFF",
            if (on) "Maintenance ON — sabke liye app band hai (aapke phone pe chalta rahega)."
            else "Maintenance OFF — app sabke liye chalu hai."
        )
    }

    private fun saveNote() {
        save(cfg.copy(updateNote = b.updateNoteInput.text.toString().trim()),
            "Update note badla", "Update note save ho gaya.")
    }

    private fun forceUpdate() {
        val rel = latest ?: run {
            toast("Latest APK ka pata nahi chala. Internet check karo.", error = true)
            return
        }
        Fx.dialog(this, "⚡", "Force update ON karein?",
            "v${rel.version} se purane version wale logon ka app tab tak nahi chalega jab tak wo update na karein.",
            "Haan, ON karo", {
                save(cfg.copy(minVersion = rel.version, updateNote = b.updateNoteInput.text.toString().trim()),
                    "Force update v${rel.version}", "Ab sabko v${rel.version} pe update karna padega.")
            }, "Rehne do")
    }

    private fun unforce() {
        save(cfg.copy(minVersion = 0), "Force update OFF", "Force update band kar diya.")
    }

    // ---------------- UI helpers ----------------

    private fun busy(on: Boolean) {
        b.busy.isVisible = on
        listOf(b.loginBtn, b.sendMsgBtn, b.clearMsgBtn, b.saveMaintBtn, b.saveNoteBtn,
            b.forceUpdateBtn, b.unforceBtn).forEach {
            it.isEnabled = !on
            it.alpha = if (on) 0.5f else 1f
        }
    }

    private fun toast(text: String, error: Boolean) {
        b.adminMsg.text = text
        b.adminMsg.setBackgroundResource(if (error) R.drawable.bg_msg_err else R.drawable.bg_msg_ok)
        b.adminMsg.setTextColor(getColor(if (error) R.color.err else R.color.ok))
        Fx.enter(b.adminMsg)
        b.scroll.smoothScrollTo(0, 0)
    }
}
