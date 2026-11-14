package com.sagar.videodownloader

import android.animation.ObjectAnimator
import android.animation.ValueAnimator
import android.annotation.SuppressLint
import android.app.Activity
import android.app.Dialog
import android.graphics.LinearGradient
import android.graphics.Shader
import android.os.Build
import android.view.HapticFeedbackConstants
import android.view.MotionEvent
import android.view.View
import android.view.ViewGroup
import android.view.animation.AccelerateDecelerateInterpolator
import android.view.animation.LinearInterpolator
import android.view.animation.OvershootInterpolator
import android.widget.TextView
import androidx.core.view.isVisible
import android.view.animation.PathInterpolator
import com.sagar.videodownloader.databinding.DialogPremiumBinding

/** Premium animations ke chhote helpers */
object Fx {

    fun dp(v: View, x: Int): Float = x * v.resources.displayMetrics.density

    /** Text pe gradient rang */
    fun gradientText(tv: TextView, vararg colors: Int) {
        tv.post {
            val w = tv.paint.measureText(tv.text.toString())
            tv.paint.shader = LinearGradient(0f, 0f, w, 0f, colors, null, Shader.TileMode.CLAMP)
            tv.invalidate()
        }
    }

    /** Background blobs dheere-dheere tairte rehte hain */
    fun float(v: View, dx: Float, dy: Float, duration: Long) {
        ObjectAnimator.ofFloat(v, View.TRANSLATION_X, -dx, dx).apply {
            this.duration = duration
            repeatCount = ValueAnimator.INFINITE
            repeatMode = ValueAnimator.REVERSE
            interpolator = AccelerateDecelerateInterpolator()
            start()
        }
        ObjectAnimator.ofFloat(v, View.TRANSLATION_Y, -dy, dy).apply {
            this.duration = (duration * 1.3).toLong()
            repeatCount = ValueAnimator.INFINITE
            repeatMode = ValueAnimator.REVERSE
            interpolator = AccelerateDecelerateInterpolator()
            start()
        }
    }

    /** Button ke upar chamakti line */
    fun shine(shine: View, parent: View, delay: Long = 0) {
        parent.post {
            val w = parent.width.toFloat()
            ObjectAnimator.ofFloat(shine, View.TRANSLATION_X, -dp(shine, 80), w + dp(shine, 40)).apply {
                duration = 1400
                startDelay = delay
                repeatCount = ValueAnimator.INFINITE
                repeatMode = ValueAnimator.RESTART
                interpolator = PathInterpolator(0.4f, 0f, 0.2f, 1f)
                start()
            }
        }
    }

    /** Dheere-dheere saans lene jaisa scale */
    fun pulse(v: View, to: Float = 1.08f, duration: Long = 1400) {
        ObjectAnimator.ofFloat(v, View.SCALE_X, 1f, to).apply {
            this.duration = duration; repeatCount = ValueAnimator.INFINITE
            repeatMode = ValueAnimator.REVERSE; start()
        }
        ObjectAnimator.ofFloat(v, View.SCALE_Y, 1f, to).apply {
            this.duration = duration; repeatCount = ValueAnimator.INFINITE
            repeatMode = ValueAnimator.REVERSE; start()
        }
    }

    fun spin(v: View, duration: Long = 4000) {
        ObjectAnimator.ofFloat(v, View.ROTATION, 0f, 360f).apply {
            this.duration = duration; repeatCount = ValueAnimator.INFINITE
            interpolator = LinearInterpolator(); start()
        }
    }

    fun blink(v: View) {
        ObjectAnimator.ofFloat(v, View.ALPHA, 1f, 0.3f).apply {
            duration = 800; repeatCount = ValueAnimator.INFINITE
            repeatMode = ValueAnimator.REVERSE; start()
        }
    }

    /** Neeche se upar aate hue dikhna */
    fun enter(v: View, delay: Long = 0) {
        v.isVisible = true
        v.alpha = 0f
        v.translationY = dp(v, 28)
        v.animate().alpha(1f).translationY(0f).setStartDelay(delay).setDuration(520)
            .setInterpolator(PathInterpolator(0.4f, 0f, 0.2f, 1f)).start()
    }

    fun exit(v: View, onEnd: (() -> Unit)? = null) {
        if (!v.isVisible) { onEnd?.invoke(); return }
        v.animate().alpha(0f).translationY(dp(v, 12)).setDuration(220).withEndAction {
            v.isVisible = false
            v.alpha = 1f
            v.translationY = 0f
            onEnd?.invoke()
        }.start()
    }

    fun pop(v: View, delay: Long = 0) {
        v.isVisible = true
        v.scaleX = 0f; v.scaleY = 0f; v.alpha = 0f
        v.animate().scaleX(1f).scaleY(1f).alpha(1f).setStartDelay(delay).setDuration(550)
            .setInterpolator(OvershootInterpolator(2.2f)).start()
    }

    fun shake(v: View) {
        ObjectAnimator.ofFloat(v, View.TRANSLATION_X, 0f, 18f, -18f, 12f, -12f, 6f, -6f, 0f)
            .setDuration(450).start()
    }

    /** Dabane pe button thoda chhota ho */
    @SuppressLint("ClickableViewAccessibility")
    fun pressable(vararg views: View) {
        views.forEach { v ->
            v.setOnTouchListener { view, e ->
                when (e.action) {
                    MotionEvent.ACTION_DOWN ->
                        view.animate().scaleX(0.95f).scaleY(0.95f).setDuration(90).start()
                    MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL ->
                        view.animate().scaleX(1f).scaleY(1f).setDuration(220)
                            .setInterpolator(OvershootInterpolator(3f)).start()
                }
                false
            }
        }
    }

    fun haptic(v: View, strong: Boolean = false) {
        val c = if (strong && Build.VERSION.SDK_INT >= Build.VERSION_CODES.R)
            HapticFeedbackConstants.CONFIRM else HapticFeedbackConstants.VIRTUAL_KEY
        v.performHapticFeedback(c)
    }

    /** Premium style popup */
    fun dialog(
        activity: Activity,
        emoji: String,
        title: String,
        body: String,
        primary: String,
        onPrimary: (() -> Unit)? = null,
        secondary: String? = null,
        onSecondary: (() -> Unit)? = null,
        cancelable: Boolean = true,
    ): Dialog {
        val d = Dialog(activity, R.style.PremiumDialog)
        val b = DialogPremiumBinding.inflate(activity.layoutInflater)
        d.setContentView(b.root)
        d.window?.setLayout(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)
        d.setCancelable(cancelable)
        d.setCanceledOnTouchOutside(cancelable)

        b.dEmoji.text = emoji
        b.dTitle.text = title
        b.dBody.text = body
        b.dBody.isVisible = body.isNotBlank()
        if (body.length > 350) {
            b.dScroll.layoutParams = b.dScroll.layoutParams.apply { height = dp(b.root, 300).toInt() }
        }
        b.dPrimary.text = primary
        b.dPrimary.setOnClickListener {
            if (cancelable) d.dismiss()
            onPrimary?.invoke()
        }
        if (secondary != null) {
            b.dSecondary.isVisible = true
            b.dSecondary.text = secondary
            b.dSecondary.setOnClickListener { d.dismiss(); onSecondary?.invoke() }
        }
        pressable(b.dPrimary, b.dSecondary)

        b.dialogCard.scaleX = 0.85f; b.dialogCard.scaleY = 0.85f; b.dialogCard.alpha = 0f
        d.setOnShowListener {
            b.dialogCard.animate().scaleX(1f).scaleY(1f).alpha(1f).setDuration(380)
                .setInterpolator(OvershootInterpolator(1.6f)).start()
            pulse(b.dEmoji, 1.15f, 900)
        }
        if (!activity.isFinishing) d.show()
        return d
    }
}
