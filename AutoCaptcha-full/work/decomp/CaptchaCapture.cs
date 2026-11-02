using System;
using System.Buffers.Binary;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text.Json;
using BepInEx;
using BepInEx.Core.Logging.Interpolation;
using BepInEx.Logging;
using Il2CppInterop.Runtime.InteropTypes.Arrays;

namespace NroPort.Plugin;

internal static class CaptchaCapture
{
	private sealed record Sample(byte[] Image, DateTime Received);

	private static readonly ConcurrentQueue<Sample> Pending = new ConcurrentQueue<Sample>();

	private static readonly HashSet<string> Saved = new HashSet<string>();

	internal static string Status = "Chờ CAPTCHA thật";

	internal static string Folder => Path.Combine(Paths.GameRootPath, "..", "..", "logs", "captcha-captures");

	internal static void Received(em __instance)
	{
		if (((__instance != null) ? __instance.imi : null) == null)
		{
			return;
		}
		CaptchaQueue.Publish(__instance);
		if (!Plugin.CfgCaptchaCapture.Value)
		{
			return;
		}
		try
		{
			if (((Il2CppArrayBase<byte>)(object)__instance.imi).Length != 0 && ((Il2CppArrayBase<byte>)(object)__instance.imi).Length <= 4194304 && Pending.Count < 4)
			{
				Pending.Enqueue(new Sample(((IEnumerable<byte>)__instance.imi).ToArray(), DateTime.UtcNow));
			}
		}
		catch (Exception ex)
		{
			Plugin.Log.LogWarning((object)("[CaptchaCapture] receive failed: " + ex.GetType().Name));
		}
	}

	internal static void Update()
	{
		//IL_01fe: Unknown result type (might be due to invalid IL or missing references)
		//IL_0205: Expected O, but got Unknown
		if (!Pending.TryDequeue(out var result))
		{
			return;
		}
		try
		{
			string text = Convert.ToHexString(SHA256.HashData(result.Image));
			if (!Saved.Contains(text))
			{
				bool flag = result.Image.Length >= 24 && result.Image.AsSpan(0, 8).SequenceEqual(new byte[8] { 137, 80, 78, 71, 13, 10, 26, 10 });
				bool flag2 = result.Image.Length >= 3 && result.Image[0] == byte.MaxValue && result.Image[1] == 216 && result.Image[2] == byte.MaxValue;
				int num = (flag ? BinaryPrimitives.ReadInt32BigEndian(result.Image.AsSpan(16, 4)) : 0);
				int num2 = (flag ? BinaryPrimitives.ReadInt32BigEndian(result.Image.AsSpan(20, 4)) : 0);
				string fullPath = Path.GetFullPath(Folder);
				Directory.CreateDirectory(fullPath);
				string text2 = result.Received.ToString("yyyyMMdd-HHmmss-fff") + "-" + text.Substring(0, 12);
				string text3 = text2 + (flag ? ".png" : (flag2 ? ".jpg" : ".bin"));
				File.WriteAllBytes(Path.Combine(fullPath, text3), result.Image);
				var anon = new
				{
					receivedUtc = result.Received,
					capturedUtc = DateTime.UtcNow,
					plugin = "1.4.314",
					source = "em.cdc:0x395880",
					image = text3,
					bytes = result.Image.Length,
					sha256 = text,
					format = (flag ? "PNG" : (flag2 ? "JPEG" : "UNKNOWN")),
					width = num,
					height = num2,
					map = my.mxr,
					zone = my.mxt,
					submitted = false
				};
				File.WriteAllText(Path.Combine(fullPath, text2 + ".json"), JsonSerializer.Serialize(anon, new JsonSerializerOptions
				{
					WriteIndented = true
				}));
				Saved.Add(text);
				Status = "Đã bắt ảnh CAPTCHA · " + result.Image.Length + " byte";
				ManualLogSource log = Plugin.Log;
				bool flag3 = default(bool);
				BepInExInfoLogInterpolatedStringHandler val = new BepInExInfoLogInterpolatedStringHandler(67, 5, ref flag3);
				if (flag3)
				{
					((BepInExLogInterpolatedStringHandler)val).AppendLiteral("[CaptchaCapture] saved image=");
					((BepInExLogInterpolatedStringHandler)val).AppendFormatted<string>(text3);
					((BepInExLogInterpolatedStringHandler)val).AppendLiteral(" format=");
					((BepInExLogInterpolatedStringHandler)val).AppendFormatted<string>(anon.format);
					((BepInExLogInterpolatedStringHandler)val).AppendLiteral(" size=");
					((BepInExLogInterpolatedStringHandler)val).AppendFormatted<int>(num);
					((BepInExLogInterpolatedStringHandler)val).AppendLiteral("x");
					((BepInExLogInterpolatedStringHandler)val).AppendFormatted<int>(num2);
					((BepInExLogInterpolatedStringHandler)val).AppendLiteral(" bytes=");
					((BepInExLogInterpolatedStringHandler)val).AppendFormatted<int>(result.Image.Length);
					((BepInExLogInterpolatedStringHandler)val).AppendLiteral(" submitted=False");
				}
				log.LogInfo(val);
				ds hns = df.hns;
				if (hns != null)
				{
					hns.byf("Đã lưu CAPTCHA để phân tích", 0);
				}
			}
		}
		catch (Exception ex)
		{
			Status = "Lỗi lưu mẫu CAPTCHA";
			Plugin.Log.LogWarning((object)("[CaptchaCapture] save failed: " + ex.GetType().Name));
		}
	}
}
You are not using the latest version of the tool, please update.
Latest version is '11.2.0.10050' (yours is '8.2.0.7535-95108c96')
