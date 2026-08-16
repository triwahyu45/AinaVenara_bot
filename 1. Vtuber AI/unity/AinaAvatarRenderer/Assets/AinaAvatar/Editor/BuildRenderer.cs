using System.IO;
using Aina.Avatar;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace Aina.Editor
{
    public static class BuildRenderer
    {
        const string ScenePath = "Assets/AinaAvatarRenderer.unity";

        [MenuItem("Aina/Create Renderer Scene")]
        public static void CreateScene()
        {
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var camera = new GameObject("Main Camera").AddComponent<Camera>();
            camera.tag = "MainCamera";
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(0f, 0f, 0f, 0f);
            camera.allowHDR = false;
            camera.transform.position = new Vector3(0f, 1.25f, -2.8f);
            camera.transform.rotation = Quaternion.identity;

            var light = new GameObject("Directional Light").AddComponent<Light>();
            light.type = LightType.Directional;
            light.intensity = 1f;
            light.shadows = LightShadows.None;
            light.transform.rotation = Quaternion.Euler(35f, -25f, 0f);

            var root = new GameObject("AinaAvatarRoot");
            var anchor = new GameObject("ModelAnchor").transform;
            anchor.SetParent(root.transform);
            var animator = root.AddComponent<ProceduralAvatarAnimator>();
            var loader = root.AddComponent<VrmAvatarLoader>();
            loader.anchor = anchor;
            loader.proceduralAnimator = animator;
            var window = root.AddComponent<WindowControllerBridge>();
            var desktop = root.AddComponent<DesktopInteraction>();
            desktop.avatarCamera = camera;
            var animationLibrary = root.AddComponent<VrmaAnimationLibrary>();
            animationLibrary.avatarLoader = loader;

            var canvas = new GameObject("Subtitle Canvas").AddComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvas.gameObject.AddComponent<CanvasScaler>();
            canvas.gameObject.AddComponent<GraphicRaycaster>();
            var panel = new GameObject("Bubble").AddComponent<Image>();
            panel.transform.SetParent(canvas.transform, false);
            panel.color = new Color(0.08f, 0.08f, 0.12f, 0.86f);
            var rect = panel.rectTransform;
            rect.anchorMin = new Vector2(0.08f, 0.05f);
            rect.anchorMax = new Vector2(0.92f, 0.22f);
            rect.offsetMin = rect.offsetMax = Vector2.zero;
            var text = new GameObject("Text").AddComponent<Text>();
            text.transform.SetParent(panel.transform, false);
            text.alignment = TextAnchor.MiddleCenter;
            text.font = Resources.GetBuiltinResource<Font>("Arial.ttf");
            text.color = Color.white;
            text.resizeTextForBestFit = true;
            text.rectTransform.anchorMin = Vector2.zero;
            text.rectTransform.anchorMax = Vector2.one;
            text.rectTransform.offsetMin = new Vector2(18f, 12f);
            text.rectTransform.offsetMax = new Vector2(-18f, -12f);
            var bubble = canvas.gameObject.AddComponent<SubtitleBubble>();
            bubble.label = text;
            bubble.panel = panel;
            panel.gameObject.SetActive(false);

            var socket = root.AddComponent<AvatarWebSocketClient>();
            socket.loader = loader;
            socket.animator = animator;
            socket.bubble = bubble;
            socket.windowController = window;
            socket.animationLibrary = animationLibrary;

            new GameObject("EventSystem", typeof(EventSystem), typeof(StandaloneInputModule));
            EditorSceneManager.SaveScene(scene, ScenePath);
            PlayerSettings.productName = "AinaAvatarRenderer";
            PlayerSettings.companyName = "TriWahyu45";
            PlayerSettings.defaultScreenWidth = 540;
            PlayerSettings.defaultScreenHeight = 720;
            PlayerSettings.runInBackground = true;
            PlayerSettings.resizableWindow = true;
            QualitySettings.shadows = ShadowQuality.Disable;
        }

        [MenuItem("Aina/Build Windows Renderer")]
        public static void BuildWindows()
        {
            CreateScene();
            Directory.CreateDirectory("Build");
            var report = BuildPipeline.BuildPlayer(
                new[] { ScenePath },
                "Build/AinaAvatarRenderer.exe",
                BuildTarget.StandaloneWindows64,
                BuildOptions.None
            );
            if (report.summary.result != BuildResult.Succeeded)
                throw new BuildFailedException("Aina renderer build gagal.");
        }

        public static void BuildWindowsCommandLine() => BuildWindows();
    }
}
