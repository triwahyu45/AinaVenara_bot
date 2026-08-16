using System;
using System.Reflection;
using UnityEngine;

namespace Aina.Avatar
{
    public class WindowControllerBridge : MonoBehaviour
    {
        Component controller;

        void Awake()
        {
            var type = FindType("UniWindowController");
            if (type == null)
            {
                Debug.LogWarning("UniWindowController tidak ditemukan.");
                return;
            }
            controller = gameObject.GetComponent(type) ?? gameObject.AddComponent(type);
            Set("isTransparent", true);
            Set("isTopmost", true);
            Set("isBorderless", true);
        }

        public void Apply(bool clickThrough, bool alwaysOnTop)
        {
            Set("isClickThrough", clickThrough);
            Set("isTopmost", alwaysOnTop);
        }

        void Set(string property, object value)
        {
            if (controller == null) return;
            var prop = controller.GetType().GetProperty(
                property,
                BindingFlags.IgnoreCase | BindingFlags.Public | BindingFlags.Instance
            );
            if (prop != null && prop.CanWrite) prop.SetValue(controller, value);
            var field = controller.GetType().GetField(
                property,
                BindingFlags.IgnoreCase | BindingFlags.Public | BindingFlags.Instance
            );
            if (field != null) field.SetValue(controller, value);
        }

        static Type FindType(string name)
        {
            foreach (var assembly in AppDomain.CurrentDomain.GetAssemblies())
            {
                var found = assembly.GetType(name);
                if (found != null) return found;
                foreach (var type in assembly.GetTypes())
                    if (type.Name == name) return type;
            }
            return null;
        }
    }
}
