using Aina.Avatar;
using NUnit.Framework;
using UnityEngine;

namespace Aina.Tests
{
    public class AvatarEventTests
    {
        [Test]
        public void ParseEmotionEvent()
        {
            var message = JsonUtility.FromJson<AvatarEvent>(
                "{\"type\":\"emotion\",\"value\":\"marah\",\"intensity\":0.8,\"duration_ms\":3500}"
            );
            Assert.AreEqual("emotion", message.type);
            Assert.AreEqual("marah", message.value);
            Assert.AreEqual(0.8f, message.intensity);
        }

        [Test]
        public void ParseConfigEvent()
        {
            var message = JsonUtility.FromJson<AvatarEvent>(
                "{\"type\":\"config\",\"bubble\":false,\"click_through\":true,\"fps\":30}"
            );
            Assert.IsFalse(message.bubble);
            Assert.IsTrue(message.click_through);
            Assert.AreEqual(30f, message.fps);
        }

        [Test]
        public void ParseAudioLevelEvent()
        {
            var message = JsonUtility.FromJson<AvatarEvent>(
                "{\"type\":\"audio_level\",\"value\":0.42}"
            );
            Assert.AreEqual("audio_level", message.type);
            Assert.AreEqual(0.42f, message.value);
        }

        [Test]
        public void ParseAnimationEvent()
        {
            var message = JsonUtility.FromJson<AvatarEvent>(
                "{\"type\":\"animation.play\",\"path\":\"C:\\\\Models\\\\wave.vrma\"}"
            );
            Assert.AreEqual("animation.play", message.type);
            Assert.AreEqual("C:\\Models\\wave.vrma", message.path);
        }
    }
}
