package com.airadb.studio

import android.annotation.SuppressLint
import android.content.Context
import android.content.Intent
import android.net.wifi.WifiManager
import android.os.Bundle
import android.provider.Settings
import android.webkit.JavascriptInterface
import android.webkit.WebChromeClient
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import java.net.InetAddress
import java.nio.ByteOrder

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private val defaultUrl = "https://airadb.onrender.com"

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        webView = WebView(this)
        setContentView(webView)

        val settings: WebSettings = webView.settings
        settings.javaScriptEnabled = true
        settings.domStorageEnabled = true
        settings.databaseEnabled = true
        settings.allowFileAccess = true
        settings.cacheMode = WebSettings.LOAD_DEFAULT
        settings.useWideViewPort = true
        settings.loadWithOverviewMode = true

        webView.webViewClient = object : WebViewClient() {
            override fun onPageFinished(view: WebView?, url: String?) {
                super.onPageFinished(view, url)
                // Inform webpage that it is running inside native Android companion app
                val ip = getWifiIpAddress()
                view?.evaluateJavascript("window.isAndroidApp = true; window.nativeDeviceIp = '$ip';", null)
            }
        }
        webView.webChromeClient = WebChromeClient()

        // Expose Native Android Bridge to JavaScript
        webView.addJavascriptInterface(WebAppInterface(this), "AndroidApp")

        webView.loadUrl(defaultUrl)
    }

    override fun onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack()
        } else {
            super.onBackPressed()
        }
    }

    private fun getWifiIpAddress(): String {
        return try {
            val wifiManager = applicationContext.getSystemService(Context.WIFI_SERVICE) as WifiManager
            var ipAddress = wifiManager.connectionInfo.ipAddress
            if (ByteOrder.nativeOrder().equals(ByteOrder.LITTLE_ENDIAN)) {
                ipAddress = Integer.reverseBytes(ipAddress)
            }
            val ipByteArray = java.math.BigInteger.valueOf(ipAddress.toLong()).toByteArray()
            InetAddress.getByAddress(ipByteArray).hostAddress ?: "127.0.0.1"
        } catch (e: Exception) {
            "127.0.0.1"
        }
    }

    inner class WebAppInterface(private val context: Context) {

        @JavascriptInterface
        fun openDeveloperOptions() {
            try {
                val intent = Intent(Settings.ACTION_APPLICATION_DEVELOPMENT_SETTINGS)
                context.startActivity(intent)
            } catch (e: Exception) {
                Toast.makeText(context, "Could not open Developer Options: ${e.message}", Toast.LENGTH_SHORT).show()
            }
        }

        @JavascriptInterface
        fun openWirelessSettings() {
            try {
                val intent = Intent(Settings.ACTION_WIRELESS_SETTINGS)
                context.startActivity(intent)
            } catch (e: Exception) {
                Toast.makeText(context, "Could not open Wireless Settings", Toast.LENGTH_SHORT).show()
            }
        }

        @JavascriptInterface
        fun getPhoneIp(): String {
            return getWifiIpAddress()
        }
    }
}
