using System.Collections;
using UnityEngine;
using UniVRM10;

namespace Aina.Avatar
{
    public class ProceduralAvatarAnimator : MonoBehaviour
    {
        Vrm10Instance instance;
        Animator animator;
        float audioLevel;
        string state = "idle";
        string emotion = "biasa";
        float emotionUntil;
        float blinkUntil;
        float nextBlink;
        Vector2 smoothLook;

        public void Bind(Vrm10Instance loaded)
        {
            instance = loaded;
            animator = loaded.GetComponent<Animator>();
            nextBlink = Time.time + Random.Range(2f, 4f);
        }

        public void SetState(string value) => state = string.IsNullOrEmpty(value) ? "idle" : value;
        public void SetAudioLevel(float value) => audioLevel = Mathf.Clamp01(value);

        public void SetEmotion(string value, float intensity, float durationMs)
        {
            emotion = string.IsNullOrEmpty(value) ? "biasa" : value;
            emotionUntil = Time.time + Mathf.Max(0.5f, durationMs / 1000f);
        }

        void Update()
        {
            if (instance == null || animator == null) return;
            if (Time.time >= emotionUntil) emotion = "biasa";
            if (Time.time >= nextBlink)
            {
                blinkUntil = Time.time + 0.12f;
                nextBlink = Time.time + Random.Range(2f, 4f);
            }
            var t = Time.time;
            var head = animator.GetBoneTransform(HumanBodyBones.Head);
            var chest = animator.GetBoneTransform(HumanBodyBones.Chest);
            if (chest != null)
            {
                var breathe = Mathf.Sin(t * 1.8f) * 1.2f;
                chest.localRotation = Quaternion.Euler(breathe, 0f, 0f);
            }
            if (head != null)
            {
                var tilt = state == "thinking" ? 8f : emotion == "malu" ? -6f : 0f;
                var mosh = emotion == "marah" ? Mathf.Sin(t * 12f) * 10f : 0f;
                var cursor = new Vector2(
                    (Input.mousePosition.x / Mathf.Max(Screen.width, 1f) - 0.5f) * 2f,
                    (Input.mousePosition.y / Mathf.Max(Screen.height, 1f) - 0.5f) * 2f
                );
                var idleEyes = new Vector2(Mathf.Sin(t * 0.45f), Mathf.Sin(t * 0.3f)) * 0.08f;
                smoothLook = Vector2.Lerp(smoothLook, cursor + idleEyes, Time.deltaTime * 2.5f);
                head.localRotation = Quaternion.Euler(
                    mosh - smoothLook.y * 5f,
                    smoothLook.x * 8f,
                    tilt
                );
            }
            SetExpression(ExpressionPreset.aa, audioLevel);
            SetExpression(ExpressionPreset.blink, Time.time < blinkUntil ? 1f : 0f);
            SetExpression(ExpressionPreset.happy, emotion == "senyum" ? 1f : 0f);
            SetExpression(ExpressionPreset.sad, emotion == "sedih" ? 1f : 0f);
            SetExpression(ExpressionPreset.angry, emotion == "marah" ? 1f : 0f);
            SetExpression(ExpressionPreset.surprised, emotion == "kaget" ? 1f : 0f);
            SetExpression(ExpressionPreset.relaxed, emotion == "malu" ? 0.65f : 0f);
        }

        void SetExpression(ExpressionPreset preset, float weight)
        {
            instance.Runtime.Expression.SetWeight(ExpressionKey.CreateFromPreset(preset), weight);
        }
    }
}
