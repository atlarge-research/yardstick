using System.Reflection;
using System.Reflection.Emit;

namespace TrProtocol;

internal static class PropertyAccessBuilder
{
    public static Action<object, object> BuildDynamicSetter(this PropertyInfo info)
    {
        if (info.SetMethod is null)
            return null;
        Type objType = info.DeclaringType;
        Type propertyType = info.PropertyType;
        var method = info.SetMethod;
        Type[] methodArgs = { typeof(object), typeof(object) };
        DynamicMethod dm = new(
            "",
            null,
            methodArgs,
            typeof(PropertyAccessBuilder).Module);

        ILGenerator il = dm.GetILGenerator();
        il.Emit(OpCodes.Ldarg_0);
        il.Emit(OpCodes.Castclass, objType);
        il.Emit(OpCodes.Ldarg_1);
        if (propertyType.IsValueType)
            il.Emit(OpCodes.Unbox_Any, propertyType);
        else
            il.Emit(OpCodes.Castclass, propertyType);
        il.Emit(OpCodes.Call, method);
        il.Emit(OpCodes.Ret);

        return dm.CreateDelegate<Action<object, object>>();
    }
    /// <summary>
    /// About 2 times slower
    /// </summary>
    /// <param name="info"></param>
    /// <returns></returns>
    public static Func<object, object> BuildDynamicGetter(this PropertyInfo info)
    {
        if (info.GetMethod is null)
            return null;
        Type objType = info.DeclaringType;
        Type propertyType = info.PropertyType;
        var method = info.GetMethod;
        Type[] methodArgs = { typeof(object) };
        DynamicMethod dm = new(
            "",
            typeof(object),
            methodArgs,
            typeof(PropertyAccessBuilder).Module);

        ILGenerator il = dm.GetILGenerator();
        il.Emit(OpCodes.Ldarg_0);
        il.Emit(OpCodes.Castclass, objType);
        il.Emit(OpCodes.Call, method);
        if (propertyType.IsValueType)
            il.Emit(OpCodes.Box, propertyType);
        il.Emit(OpCodes.Castclass, typeof(object));
        il.Emit(OpCodes.Ret);

        return dm.CreateDelegate<Func<object, object>>();
    }
}
