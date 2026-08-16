using System;
using System.Threading.Tasks;
using UnityEngine;
using UniGLTF;
using UniVRM10;

namespace Aina.Avatar
{
    public class VrmAvatarLoader : MonoBehaviour
    {
        public Transform anchor;
        public ProceduralAvatarAnimator proceduralAnimator;
        public Vrm10Instance Instance { get; private set; }
        public void SetVisible(bool visible)
        {
            if (anchor != null) anchor.gameObject.SetActive(visible);
        }

        public async Task<string> Load(string path)
        {
            if (string.IsNullOrWhiteSpace(path)) throw new ArgumentException("Path VRM kosong.");
            var loaded = await Vrm10.LoadPathAsync(
                path,
                canLoadVrm0X: true,
                awaitCaller: new RuntimeOnlyAwaitCaller()
            );
            if (Instance != null) Destroy(Instance.gameObject);
            Instance = loaded;
            Instance.transform.SetParent(anchor, false);
            Instance.transform.localPosition = Vector3.zero;
            Instance.transform.localRotation = Quaternion.Euler(0f, 180f, 0f);
            proceduralAnimator.Bind(Instance);
            return Instance.name;
        }
    }
}
