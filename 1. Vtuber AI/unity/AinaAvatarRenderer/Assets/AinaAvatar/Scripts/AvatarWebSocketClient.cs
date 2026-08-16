using System;
using System.Collections;
using NativeWebSocket;
using UnityEngine;

namespace Aina.Avatar
{
    public class AvatarWebSocketClient : MonoBehaviour
    {
        public string serverUrl = "ws://127.0.0.1:8765/avatar";
        public VrmAvatarLoader loader;
        public ProceduralAvatarAnimator animator;
        public SubtitleBubble bubble;
        public WindowControllerBridge windowController;
        public VrmaAnimationLibrary animationLibrary;
        WebSocket socket;

        async void Start() => await Connect();

        async System.Threading.Tasks.Task Connect()
        {
            try
            {
                socket = new WebSocket(serverUrl);
                socket.OnOpen += () => Send("{\"type\":\"ready\"}");
                socket.OnError += error => Debug.LogWarning(error);
                socket.OnClose += _ => StartCoroutine(Reconnect());
                socket.OnMessage += bytes => Handle(System.Text.Encoding.UTF8.GetString(bytes));
                await socket.Connect();
            }
            catch (Exception error)
            {
                Debug.LogWarning(error.Message);
                StartCoroutine(Reconnect());
            }
        }

        IEnumerator Reconnect()
        {
            yield return new WaitForSeconds(2f);
            _ = Connect();
        }

        async void Handle(string json)
        {
            var message = JsonUtility.FromJson<AvatarEvent>(json);
            try
            {
                switch (message.type)
                {
                    case "state": animator.SetState(message.value); break;
                    case "emotion": animator.SetEmotion(message.value, message.intensity, message.duration_ms); break;
                    case "audio_level": animator.SetAudioLevel(message.value); break;
                    case "subtitle": bubble.Show(message.text, message.duration_ms); break;
                    case "config":
                        bubble.Enabled = message.bubble && message.visible;
                        windowController.Apply(message.click_through, message.always_on_top);
                        Application.targetFrameRate = Mathf.RoundToInt(message.fps);
                        loader.SetVisible(message.visible);
                        break;
                    case "model.load":
                        var name = await loader.Load(message.path);
                        Send("{\"type\":\"model.loaded\",\"name\":\"" + Escape(name) + "\"}");
                        break;
                    case "animation.play":
                        await animationLibrary.Play(message.path);
                        break;
                }
            }
            catch (Exception error)
            {
                Send("{\"type\":\"error\",\"message\":\"" + Escape(error.Message) + "\"}");
            }
        }

        async void Send(string json)
        {
            if (socket != null && socket.State == WebSocketState.Open)
                await socket.SendText(json);
        }

        static string Escape(string text) => text.Replace("\\", "\\\\").Replace("\"", "\\\"");

        void Update()
        {
#if !UNITY_WEBGL || UNITY_EDITOR
            socket?.DispatchMessageQueue();
#endif
        }

        async void OnApplicationQuit()
        {
            if (socket != null) await socket.Close();
        }
    }
}
