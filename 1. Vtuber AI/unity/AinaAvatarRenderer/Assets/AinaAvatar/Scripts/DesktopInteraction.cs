using System;
using System.Diagnostics;
using System.Runtime.InteropServices;
using UnityEngine;

namespace Aina.Avatar
{
    public class DesktopInteraction : MonoBehaviour
    {
        const int WmNcLButtonDown = 0xA1;
        const int HtCaption = 0x2;
        const uint SwpNoSize = 0x0001;
        const uint SwpNoZOrder = 0x0004;
        public Camera avatarCamera;
        IntPtr window;

        [StructLayout(LayoutKind.Sequential)]
        struct Rect { public int Left, Top, Right, Bottom; }

        [DllImport("user32.dll")] static extern bool ReleaseCapture();
        [DllImport("user32.dll")] static extern IntPtr SendMessage(IntPtr hWnd, int msg, int wParam, int lParam);
        [DllImport("user32.dll")] static extern bool GetWindowRect(IntPtr hWnd, out Rect rect);
        [DllImport("user32.dll")] static extern bool SetWindowPos(IntPtr hWnd, IntPtr insertAfter, int x, int y, int cx, int cy, uint flags);

        void Start()
        {
            window = Process.GetCurrentProcess().MainWindowHandle;
            if (window != IntPtr.Zero)
                SetWindowPos(window, IntPtr.Zero, PlayerPrefs.GetInt("window.x", 40), PlayerPrefs.GetInt("window.y", 80), 0, 0, SwpNoSize | SwpNoZOrder);
            if (avatarCamera != null) avatarCamera.fieldOfView = PlayerPrefs.GetFloat("camera.fov", 35f);
        }

        void Update()
        {
            if (Input.GetMouseButtonDown(0) && window != IntPtr.Zero)
            {
                ReleaseCapture();
                SendMessage(window, WmNcLButtonDown, HtCaption, 0);
            }
            var wheel = Input.mouseScrollDelta.y;
            if (Mathf.Abs(wheel) > 0.01f && avatarCamera != null)
            {
                avatarCamera.fieldOfView = Mathf.Clamp(avatarCamera.fieldOfView - wheel * 2f, 18f, 65f);
                PlayerPrefs.SetFloat("camera.fov", avatarCamera.fieldOfView);
            }
        }

        void OnApplicationQuit()
        {
            if (window != IntPtr.Zero && GetWindowRect(window, out var rect))
            {
                PlayerPrefs.SetInt("window.x", rect.Left);
                PlayerPrefs.SetInt("window.y", rect.Top);
            }
            PlayerPrefs.Save();
        }
    }
}

