using System.IO;
using System.Threading.Tasks;
using UnityEngine;
using UniGLTF;
using UniVRM10;

namespace Aina.Avatar
{
    public class VrmaAnimationLibrary : MonoBehaviour
    {
        public string animationsFolder = "animations";
        public VrmAvatarLoader avatarLoader;
        GameObject currentAnimation;

        public string[] Available()
        {
            var folder = Path.Combine(Application.persistentDataPath, animationsFolder);
            Directory.CreateDirectory(folder);
            return Directory.GetFiles(folder, "*.vrma");
        }

        public async Task Play(string path)
        {
            if (avatarLoader == null || avatarLoader.Instance == null)
                throw new System.InvalidOperationException("Load model VRM sebelum memainkan VRMA.");
            using GltfData data = new AutoGltfFileParser(path).Parse();
            using var loader = new VrmAnimationImporter(data);
            var instance = await loader.LoadAsync(new ImmediateCaller());
            if (currentAnimation != null) Destroy(currentAnimation);
            currentAnimation = instance;
            avatarLoader.Instance.Runtime.VrmAnimation =
                instance.GetComponent<Vrm10AnimationInstance>();
            instance.GetComponent<Animation>().Play();
        }
    }
}
