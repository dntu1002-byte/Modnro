using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Security.Cryptography;
using System.Text.Json;
using BepInEx;
using BepInEx.Core.Logging.Interpolation;
using BepInEx.Logging;
using HarmonyLib;
using Il2CppInterop.Runtime.InteropTypes;
using Il2CppInterop.Runtime.InteropTypes.Arrays;
using Il2CppSystem;
using UnityEngine;

namespace NroPort.Plugin;

internal static class CaptchaQueue
{
	private static readonly HashSet<string> Published = new HashSet<string>();

	private static IntPtr _panel;

	private static string _hash;

	private static long _waitLogs;

	private static double _nextTry;

	private static long _lenLogs;

	private static int _hashLength;

	private static bool _autoSubmit;

	private static int _attempts;

	private static string _lastAnswer;

	private static DateTime _lastSubmitUtc = DateTime.MinValue;

	private static DateTime _publishedUtc = DateTime.MinValue;

	private static bool _timeoutLogged;

	private static DateTime _notBeforeUtc = DateTime.MinValue;

	internal static string Status = "Chờ CAPTCHA";

	private static string Root => Path.Combine(Paths.GameRootPath, "tudzday-captcha");

	internal static void Install(Harmony harmony)
	{
		//IL_0032: Unknown result type (might be due to invalid IL or missing references)
		//IL_0040: Expected O, but got Unknown
		try
		{
			MethodInfo methodInfo = AccessTools.Method(typeof(em), "bbo", (Type[])null, (Type[])null);
			if (methodInfo != null)
			{
				harmony.Patch((MethodBase)methodInfo, new HarmonyMethod(typeof(CaptchaQueue), "BboPrefix", (Type[])null), (HarmonyMethod)null, (HarmonyMethod)null, (HarmonyMethod)null, (HarmonyMethod)null);
			}
			Plugin.Log.LogInfo((object)"[CaptchaQueue] hooked em.bbo (ghi nhan mau captcha khi nguoi dung gui).");
		}
		catch (Exception ex)
		{
			Plugin.Log.LogWarning((object)("[CaptchaQueue] install failed: " + ex.GetType().Name));
		}
	}

	internal static void BboPrefix(em __instance, object[] __args)
	{
		//IL_00e6: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ed: Expected O, but got Unknown
		try
		{
			if (_autoSubmit || __args == null || __args.Length < 1 || !(__args[0] is int num) || num != 1)
			{
				return;
			}
			string text = ((__instance != null) ? __instance.imf : null);
			if (string.IsNullOrEmpty(text) || text.Length > 8)
			{
				return;
			}
			string text2 = _hash;
			if (string.IsNullOrEmpty(text2) && ((__instance != null) ? __instance.imi : null) != null)
			{
				text2 = Hashing(Il2CppArrayBase<byte>.op_Implicit((Il2CppArrayBase<byte>)(object)__instance.imi));
			}
			if (!string.IsNullOrEmpty(text2))
			{
				Directory.CreateDirectory(Root);
				File.AppendAllText(Path.Combine(Root, "labels.jsonl"), JsonSerializer.Serialize(new
				{
					hash = text2,
					answer = text,
					timeUtc = DateTime.UtcNow.ToString("O"),
					pid = Environment.ProcessId
				}) + Environment.NewLine);
				ManualLogSource log = Plugin.Log;
				bool flag = default(bool);
				BepInExInfoLogInterpolatedStringHandler val = new BepInExInfoLogInterpolatedStringHandler(22, 2, ref flag);
				if (flag)
				{
					((BepInExLogInterpolatedStringHandler)val).AppendLiteral("[CaptchaQueue] label ");
					((BepInExLogInterpolatedStringHandler)val).AppendFormatted<string>(text2);
					((BepInExLogInterpolatedStringHandler)val).AppendLiteral(" ");
					((BepInExLogInterpolatedStringHandler)val).AppendFormatted<string>(text);
				}
				log.LogInfo(val);
			}
		}
		catch
		{
		}
	}

	internal static void Publish(em panel)
	{
		//IL_0272: Unknown result type (might be due to invalid IL or missing references)
		//IL_0279: Expected O, but got Unknown
		//IL_016c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0173: Expected O, but got Unknown
		try
		{
			if (((panel != null) ? panel.imi : null) == null || ((Il2CppArrayBase<byte>)(object)panel.imi).Length == 0)
			{
				return;
			}
			string text = Hashing(Il2CppArrayBase<byte>.op_Implicit((Il2CppArrayBase<byte>)(object)panel.imi));
			string text2 = Path.Combine(Root, "inbox");
			string text3 = Path.Combine(Root, "jobs");
			Directory.CreateDirectory(text2);
			Directory.CreateDirectory(text3);
			_panel = ((Il2CppObjectBase)panel).Pointer;
			_hash = text;
			if (!Published.Add(text))
			{
				return;
			}
			_attempts = 0;
			_lastAnswer = null;
			_lastSubmitUtc = DateTime.MinValue;
			_publishedUtc = DateTime.UtcNow;
			_timeoutLogged = false;
			_waitLogs = 0L;
			string path = Path.Combine(text2, text + ".png");
			if (!File.Exists(path))
			{
				File.WriteAllBytes(path, Il2CppArrayBase<byte>.op_Implicit((Il2CppArrayBase<byte>)(object)panel.imi));
			}
			File.WriteAllText(Path.Combine(text3, text + ".json"), JsonSerializer.Serialize(new
			{
				hash = text,
				pid = Environment.ProcessId,
				timeUtc = DateTime.UtcNow.ToString("O"),
				map = my.mxr,
				zone = my.mxt,
				bytes = ((Il2CppArrayBase<byte>)(object)panel.imi).Length,
				answerLength = ExpectedLength(panel),
				plugin = "1.4.314"
			}));
			_notBeforeUtc = DateTime.UtcNow.AddSeconds(2.5);
			Status = "Đã đưa ảnh CAPTCHA cho tool";
			bool flag = default(bool);
			BepInExInfoLogInterpolatedStringHandler val;
			try
			{
				mx imk = panel.imk;
				ManualLogSource log = Plugin.Log;
				val = new BepInExInfoLogInterpolatedStringHandler(58, 6, ref flag);
				if (flag)
				{
					((BepInExLogInterpolatedStringHandler)val).AppendLiteral("[CaptchaQueue] field mvd='");
					((BepInExLogInterpolatedStringHandler)val).AppendFormatted<string>((imk != null) ? imk.mvd : null);
					((BepInExLogInterpolatedStringHandler)val).AppendLiteral("' mve='");
					((BepInExLogInterpolatedStringHandler)val).AppendFormatted<string>((imk != null) ? imk.mve : null);
					((BepInExLogInterpolatedStringHandler)val).AppendLiteral("' mvi='");
					((BepInExLogInterpolatedStringHandler)val).AppendFormatted<string>((imk != null) ? imk.mvi : null);
					((BepInExLogInterpolatedStringHandler)val).AppendLiteral("' mvj='");
					((BepInExLogInterpolatedStringHandler)val).AppendFormatted<string>((imk != null) ? imk.mvj : null);
					((BepInExLogInterpolatedStringHandler)val).AppendLiteral("' mvf=");
					((BepInExLogInterpolatedStringHandler)val).AppendFormatted<int?>((imk != null) ? new int?(imk.mvf) : null);
					((BepInExLogInterpolatedStringHandler)val).AppendLiteral(" mvg=");
					((BepInExLogInterpolatedStringHandler)val).AppendFormatted<int?>((imk != null) ? new int?(imk.mvg) : null);
				}
				log.LogInfo(val);
			}
			catch
			{
			}
			ManualLogSource log2 = Plugin.Log;
			val = new BepInExInfoLogInterpolatedStringHandler(39, 3, ref flag);
			if (flag)
			{
				((BepInExLogInterpolatedStringHandler)val).AppendLiteral("[CaptchaQueue] publish ");
				((BepInExLogInterpolatedStringHandler)val).AppendFormatted<string>(text);
				((BepInExLogInterpolatedStringHandler)val).AppendLiteral(" ");
				((BepInExLogInterpolatedStringHandler)val).AppendFormatted<int>(((Il2CppArrayBase<byte>)(object)panel.imi).Length);
				((BepInExLogInterpolatedStringHandler)val).AppendLiteral("B -> inbox/");
				((BepInExLogInterpolatedStringHandler)val).AppendFormatted<string>(text);
				((BepInExLogInterpolatedStringHandler)val).AppendLiteral(".png");
			}
			log2.LogInfo(val);
		}
		catch (Exception ex)
		{
			Plugin.Log.LogWarning((object)("[CaptchaQueue] publish failed: " + ex.GetType().Name));
		}
	}

	internal static void Tick()
	{
		//IL_03f3: Unknown result type (might be due to invalid IL or missing references)
		//IL_03fa: Expected O, but got Unknown
		//IL_0282: Unknown result type (might be due to invalid IL or missing references)
		//IL_0289: Expected O, but got Unknown
		if (!Plugin.CfgCaptchaAuto.Value)
		{
			return;
		}
		em val = null;
		try
		{
			val = em.ima;
		}
		catch
		{
		}
		if (val == null)
		{
			val = CaptchaBlocker.Hidden;
		}
		if (CaptchaBlocker.Hidden != null && (DateTime.UtcNow - CaptchaBlocker.HiddenAt).TotalSeconds >= 12.0)
		{
			if (em.ima == null)
			{
				em.ima = CaptchaBlocker.Hidden;
				Plugin.Log.LogWarning((object)"[CaptchaQueue] 12s chưa có đáp án - hiện lại panel CAPTCHA để nhập tay.");
			}
			CaptchaBlocker.Clear();
		}
		if (val == null || val.imi == null || ((Il2CppArrayBase<byte>)(object)val.imi).Length == 0)
		{
			if (_panel != IntPtr.Zero)
			{
				_panel = IntPtr.Zero;
				_hash = null;
				CaptchaBlocker.Clear();
				Status = "Chờ CAPTCHA";
			}
			return;
		}
		if (((Il2CppObjectBase)val).Pointer != _panel || _hash == null)
		{
			_waitLogs = 0L;
			_hashLength = 0;
			_attempts = 0;
			_lastAnswer = null;
			_lastSubmitUtc = DateTime.MinValue;
			_timeoutLogged = false;
			_publishedUtc = DateTime.UtcNow;
			_notBeforeUtc = DateTime.UtcNow.AddSeconds(2.5);
			Publish(val);
		}
		if (val.imh)
		{
			return;
		}
		int num = ExpectedLength(val);
		bool flag = default(bool);
		if (num > 0 && _hash != null && _hashLength != num)
		{
			_hashLength = num;
			try
			{
				string path = Path.Combine(Root, "jobs", _hash + ".json");
				if (File.Exists(path))
				{
					JsonDocument jsonDocument = JsonDocument.Parse(File.ReadAllText(path));
					Dictionary<string, object> dictionary = new Dictionary<string, object>();
					foreach (JsonProperty item in jsonDocument.RootElement.EnumerateObject())
					{
						dictionary[item.Name] = ((item.Value.ValueKind == JsonValueKind.Number) ? ((object)item.Value.GetInt64()) : ((item.Value.ValueKind == JsonValueKind.String) ? item.Value.GetString() : item.Value.ToString()));
					}
					dictionary["answerLength"] = num;
					File.WriteAllText(path, JsonSerializer.Serialize(dictionary));
					ManualLogSource log = Plugin.Log;
					BepInExInfoLogInterpolatedStringHandler val2 = new BepInExInfoLogInterpolatedStringHandler(32, 2, ref flag);
					if (flag)
					{
						((BepInExLogInterpolatedStringHandler)val2).AppendLiteral("[CaptchaQueue] answerLength=");
						((BepInExLogInterpolatedStringHandler)val2).AppendFormatted<int>(num);
						((BepInExLogInterpolatedStringHandler)val2).AppendLiteral(" -> ");
						((BepInExLogInterpolatedStringHandler)val2).AppendFormatted<string>(_hash);
					}
					log.LogInfo(val2);
				}
			}
			catch
			{
			}
		}
		string text = _hash ?? Hashing(Il2CppArrayBase<byte>.op_Implicit((Il2CppArrayBase<byte>)(object)val.imi));
		string path2 = Path.Combine(Root, "outbox", text + ".txt");
		string path3 = Path.Combine(Root, "outbox", text + ".alt.txt");
		int num2 = ExpectedLength(val);
		if (_attempts == 0)
		{
			if (!TryReadAnswer(path2, out var answer))
			{
				if (_waitLogs < 6)
				{
					_waitLogs++;
					Plugin.Log.LogInfo((object)("[CaptchaQueue] chờ tool trả đáp án " + _hash));
				}
				if (!_timeoutLogged && (DateTime.UtcNow - _publishedUtc).TotalSeconds >= 20.0)
				{
					_timeoutLogged = true;
					Status = "Chưa có đáp án CAPTCHA (tool chưa trả lời)";
					Plugin.Log.LogWarning((object)("[CaptchaQueue] 20s chưa có đáp án cho " + _hash + " - panel vẫn mở, cần nhập tay."));
				}
				return;
			}
			if (num2 > 0 && answer.Length != num2)
			{
				if (_lenLogs < 3)
				{
					_lenLogs++;
					ManualLogSource log2 = Plugin.Log;
					BepInExWarningLogInterpolatedStringHandler val3 = new BepInExWarningLogInterpolatedStringHandler(38, 3, ref flag);
					if (flag)
					{
						((BepInExLogInterpolatedStringHandler)val3).AppendLiteral("[CaptchaQueue] bỏ đáp án ");
						((BepInExLogInterpolatedStringHandler)val3).AppendFormatted<string>(answer);
						((BepInExLogInterpolatedStringHandler)val3).AppendLiteral(" (dài ");
						((BepInExLogInterpolatedStringHandler)val3).AppendFormatted<int>(answer.Length);
						((BepInExLogInterpolatedStringHandler)val3).AppendLiteral(", cần ");
						((BepInExLogInterpolatedStringHandler)val3).AppendFormatted<int>(num2);
						((BepInExLogInterpolatedStringHandler)val3).AppendLiteral(")");
					}
					log2.LogWarning(val3);
				}
				return;
			}
			double unscaledTimeAsDouble = Time.unscaledTimeAsDouble;
			if (unscaledTimeAsDouble < _nextTry || DateTime.UtcNow < _notBeforeUtc)
			{
				return;
			}
			_nextTry = unscaledTimeAsDouble + 2.0;
			if (Submit(val, answer))
			{
				try
				{
					File.Delete(path2);
				}
				catch
				{
				}
			}
		}
		else if (_attempts == 1)
		{
			if ((DateTime.UtcNow - _lastSubmitUtc).TotalSeconds < 5.0)
			{
				return;
			}
			if (!TryReadAnswer(path3, out var answer2) || answer2 == _lastAnswer)
			{
				if (!_timeoutLogged)
				{
					_timeoutLogged = true;
					Status = "Đáp án đầu chưa được nhận, không có đáp án dự phòng";
					Plugin.Log.LogWarning((object)("[CaptchaQueue] panel vẫn mở sau khi gửi " + _lastAnswer + " và không có đáp án dự phòng."));
				}
			}
			else
			{
				if (num2 > 0 && answer2.Length != num2)
				{
					return;
				}
				double unscaledTimeAsDouble2 = Time.unscaledTimeAsDouble;
				if (unscaledTimeAsDouble2 < _nextTry || DateTime.UtcNow < _notBeforeUtc)
				{
					return;
				}
				_nextTry = unscaledTimeAsDouble2 + 2.0;
				Plugin.Log.LogInfo((object)("[CaptchaQueue] thử lại với đáp án dự phòng " + answer2 + " (đáp án đầu " + _lastAnswer + " chưa đóng panel)."));
				if (Submit(val, answer2))
				{
					try
					{
						File.Delete(path3);
					}
					catch
					{
					}
				}
			}
		}
		else if (!_timeoutLogged)
		{
			_timeoutLogged = true;
			Status = "Đã thử 2 đáp án CAPTCHA";
			Plugin.Log.LogWarning((object)("[CaptchaQueue] đã gửi 2 đáp án cho " + _hash + ", panel vẫn mở - dừng tự gửi để tránh khóa."));
		}
	}

	private static bool TryReadAnswer(string path, out string answer)
	{
		answer = null;
		try
		{
			if (!File.Exists(path))
			{
				return false;
			}
			string text = File.ReadAllText(path).Trim();
			int length = text.Length;
			if ((length < 3 || length > 8) ? true : false)
			{
				return false;
			}
			string text2 = text;
			for (length = 0; length < text2.Length; length++)
			{
				if (!char.IsLetterOrDigit(text2[length]))
				{
					return false;
				}
			}
			answer = text;
			return true;
		}
		catch
		{
			return false;
		}
	}

	private static bool Submit(em panel, string answer)
	{
		try
		{
			mx imk = panel.imk;
			if (imk != null)
			{
				imk.ema(answer);
			}
		}
		catch (Exception ex)
		{
			Plugin.Log.LogWarning((object)("[CaptchaQueue] set field failed: " + ex.Message));
		}
		try
		{
			panel.imf = answer;
		}
		catch (Exception ex2)
		{
			Plugin.Log.LogWarning((object)("[CaptchaQueue] set imf failed: " + ex2.Message));
		}
		_autoSubmit = true;
		try
		{
			panel.bbo(1, (Object)null);
			_attempts++;
			_lastAnswer = answer;
			_lastSubmitUtc = DateTime.UtcNow;
			Status = "Đã gửi CAPTCHA " + answer;
			Plugin.Log.LogInfo((object)("[CaptchaQueue] submit " + answer + " (lan " + _attempts + ")"));
			if (CaptchaBlocker.Hidden != null && ((Il2CppObjectBase)CaptchaBlocker.Hidden).Pointer == ((Il2CppObjectBase)panel).Pointer)
			{
				CaptchaBlocker.Clear();
			}
			return true;
		}
		catch (Exception ex3)
		{
			Status = "Gửi CAPTCHA lỗi";
			Plugin.Log.LogWarning((object)("[CaptchaQueue] submit failed: " + ex3.GetType().Name + " | " + ex3.Message));
			return false;
		}
		finally
		{
			_autoSubmit = false;
		}
	}

	private static int ExpectedLength(em panel)
	{
		try
		{
			object obj;
			if (panel == null)
			{
				obj = null;
			}
			else
			{
				mx imk = panel.imk;
				obj = ((imk != null) ? imk.mvd : null);
			}
			string text = (string)obj;
			if (string.IsNullOrEmpty(text) || text.Length > 8)
			{
				return 0;
			}
			string text2 = text;
			for (int i = 0; i < text2.Length; i++)
			{
				if (text2[i] != '.')
				{
					return 0;
				}
			}
			return text.Length;
		}
		catch
		{
			return 0;
		}
	}

	internal static string Hashing(byte[] bytes)
	{
		return Convert.ToHexString(SHA256.HashData(bytes)).Substring(0, 16);
	}
}
You are not using the latest version of the tool, please update.
Latest version is '11.2.0.10050' (yours is '8.2.0.7535-95108c96')
