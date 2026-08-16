using System.Collections;
using UnityEngine;
using UnityEngine.UI;

namespace Aina.Avatar
{
    public class SubtitleBubble : MonoBehaviour
    {
        public Text label;
        public Image panel;
        bool enabled = true;
        public bool Enabled
        {
            get => enabled;
            set
            {
                enabled = value;
                if (!enabled && panel != null) panel.gameObject.SetActive(false);
            }
        }
        Coroutine hideRoutine;

        public void Show(string text, float durationMs)
        {
            if (!Enabled || label == null || panel == null) return;
            label.text = text;
            panel.gameObject.SetActive(true);
            if (hideRoutine != null) StopCoroutine(hideRoutine);
            hideRoutine = StartCoroutine(HideAfter(Mathf.Max(1f, durationMs / 1000f)));
        }

        IEnumerator HideAfter(float seconds)
        {
            yield return new WaitForSeconds(seconds);
            panel.gameObject.SetActive(false);
        }
    }
}
