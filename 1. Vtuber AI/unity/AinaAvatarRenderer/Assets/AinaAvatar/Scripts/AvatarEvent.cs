using System;

namespace Aina.Avatar
{
    [Serializable]
    public class AvatarEvent
    {
        public string type;
        public string value;
        public string text;
        public string path;
        public float intensity = 1f;
        public float duration_ms;
        public float fps = 30f;
        public bool bubble = true;
        public bool click_through;
        public bool always_on_top = true;
        public bool visible = true;
    }
}
