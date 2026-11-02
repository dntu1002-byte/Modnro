// ============================================================================
// NRO AUTO CAPTCHA (5 & 6 SO) - TICH HOP TRUC TIEP VAO MOD-250-PC (100% C#)
// Khong can Python, khong phu thuoc duong dan C:\Users\..., nguoi khac tai Mod
// ve chi can mo NroPort.exe la tu dong giai va bam 5 nut cam 1, 3, 5, 7, 9!
// ============================================================================
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.IO.Compression;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;

#if BEPINEX_IL2CPP
using BepInEx;
using BepInEx.Unity.IL2CPP;

namespace NroAutoCaptchaMod
{
    [BepInPlugin("nro.autocaptcha.embedded", "NRO Auto Captcha Embedded (5-6 Digits)", "8.1.0")]
    public class AAA_NroAutoCaptchaPlugin : BasePlugin
    {
        static AAA_NroAutoCaptchaPlugin()
        {
            try { CaptchaEmbeddedEngine.EnsureRelativeConfigAndStart(); } catch (Exception) { }
        }

        public override void Load()
        {
            try
            {
                CaptchaEmbeddedEngine.EnsureRelativeConfigAndStart();
                Log.LogInfo("[NRO-AutoCaptcha] Da kich hoat ben trong Mod (IL2CPP)!");
            }
            catch (Exception ex)
            {
                Log.LogError("[NRO-AutoCaptcha] Loi Load: " + ex.Message);
            }
        }
    }
}
#elif BEPINEX_PLUGIN
using BepInEx;
using UnityEngine;

namespace NroAutoCaptchaMod
{
    [BepInPlugin("nro.autocaptcha.embedded", "NRO Auto Captcha Embedded (5-6 Digits)", "8.1.0")]
    public class AAA_NroAutoCaptchaPlugin : BaseUnityPlugin
    {
        static AAA_NroAutoCaptchaPlugin()
        {
            try { CaptchaEmbeddedEngine.EnsureRelativeConfigAndStart(); } catch (Exception) { }
        }

        private void Awake()
        {
            try
            {
                CaptchaEmbeddedEngine.EnsureRelativeConfigAndStart();
                Logger.LogInfo("[NRO-AutoCaptcha] Da kich hoat thanh cong ben trong Mod-250-PC!");
            }
            catch (Exception ex)
            {
                Logger.LogError("[NRO-AutoCaptcha] Loi Awake: " + ex.Message);
            }
        }
    }
}
#endif

namespace NroAutoCaptchaMod
{
    public class CompItem
    {
        public int X;
        public int Y;
        public int W;
        public int H;
        public int Area;
        public double XMean;
        public List<int[]> Pixels;
    }

    public class ClusterItem
    {
        public double XMean;
        public double Area;
        public int X;
        public int Y;
        public int W;
        public int H;

        public ClusterItem(double xm, double a, int x, int y, int w, int h)
        {
            XMean = xm; Area = a; X = x; Y = y; W = w; H = h;
        }
    }

    public class LegendEntry
    {
        public string Cell;
        public string ColorName;
        public string Symbol;
        public string Digit;
        public double SymScore;
        public double DigScore;
        public Dictionary<string, double> AllDigScores;
        public Dictionary<string, double> AllSymScores;
    }

    public class TopDetectedItem
    {
        public double X;
        public string Color;
        public string Symbol;
        public double SymScore;
        public string AltSymbol;
        public double AltScore;
        public double Area;
        public int W;
        public int H;
    }

    public static class CaptchaEmbeddedEngine
    {
        private static bool _started = false;
        private static readonly object _lockObj = new object();
        private static Mutex _singleInstanceMutex = null;

        private static readonly string[] ORDER = new string[] { "W", "Y", "M", "G", "B", "R", "K" };
        private static readonly string[] ODD_DIGITS = new string[] { "1", "3", "5", "7", "9" };
        private static readonly string XHEIGHT_LOWER = "acemnorsuvwxz";
        private static readonly string TALL_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZbdfghijklpqty@#%&";

        private static readonly double[] ORANGE_BTN_X_PCTS = new double[] { 0.3529, 0.4321, 0.5123, 0.5916, 0.6728 };
        private static readonly double ORANGE_BTN_Y_PCT = 0.9015;

        private static readonly Dictionary<string, string[]> BUILTIN_DIGIT_BITMAPS = new Dictionary<string, string[]>
        {
            { "1", new string[] {
                ".....##.....", "...####.....", ".######.....", ".######.....", ".....##.....", ".....##.....",
                ".....##.....", ".....##.....", ".....##.....", ".....##.....", ".....##.....", ".....##.....",
                ".##########.", ".##########.", ".##########.", "............"
            }},
            { "3", new string[] {
                "..#######...", ".#########..", ".###...####.", "........###.", "........###.", ".......###..",
                "...######...", "...######...", ".......####.", "........###.", "........###.", "........###.",
                ".###...####.", ".#########..", "..#######...", "............"
            }},
            { "5", new string[] {
                "..########..", "..########..", "..##........", "..##........", "..##........", "..#######...",
                "..########..", "...########.", "........###.", "........###.", "........###.", "........###.",
                ".###...####.", ".#########..", "..#######...", "............"
            }},
            { "7", new string[] {
                ".##########.", ".##########.", "........###.", ".......###..", ".......###..", "......###...",
                ".....###....", ".....###....", "....###.....", "....###.....", "...###......", "...###......",
                "...###......", "..###.......", "..###.......", "............"
            }},
            { "9", new string[] {
                "..#######...", ".#########..", ".###...####.", "###.....###.", "###.....###.", "###.....###.",
                ".####..####.", "..#########.", "...#####.##.", "........###.", "........###.", ".......###..",
                ".###..####..", ".########...", "..######....", "............"
            }}
        };

        private const string PACKED_TEMPLATES_B64 = "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";

        private static Dictionary<string, List<int[,]>> _digitBank;
        private static Dictionary<string, List<int[,]>> _uprightSymBank;
        private static Dictionary<string, List<int[,]>> _rotatedSymBank;

        [DllImport("user32.dll")]
        private static extern bool IsWindowVisible(IntPtr hWnd);
        [DllImport("user32.dll")]
        private static extern bool IsIconic(IntPtr hWnd);
        [DllImport("user32.dll")]
        private static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
        [DllImport("user32.dll")]
        private static extern bool SetForegroundWindow(IntPtr hWnd);
        [DllImport("user32.dll")]
        private static extern IntPtr GetForegroundWindow();
        [DllImport("user32.dll")]
        private static extern bool BringWindowToTop(IntPtr hWnd);
        [DllImport("user32.dll")]
        private static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);
        [DllImport("user32.dll")]
        private static extern IntPtr GetDC(IntPtr hWnd);
        [DllImport("user32.dll")]
        private static extern int ReleaseDC(IntPtr hWnd, IntPtr hDC);
        [DllImport("gdi32.dll")]
        private static extern uint GetPixel(IntPtr hdc, int nXPos, int nYPos);
        [DllImport("user32.dll")]
        private static extern bool AttachThreadInput(uint idAttach, uint idAttachTo, bool fAttach);
        [DllImport("kernel32.dll")]
        private static extern uint GetCurrentThreadId();
        [DllImport("user32.dll")]
        private static extern bool GetClientRect(IntPtr hWnd, out RECT lpRect);
        [DllImport("user32.dll")]
        private static extern bool ClientToScreen(IntPtr hWnd, ref POINT lpPoint);
        [DllImport("user32.dll")]
        private static extern bool SetCursorPos(int X, int Y);
        [DllImport("user32.dll")]
        private static extern bool GetCursorPos(out POINT lpPoint);
        [DllImport("user32.dll")]
        private static extern bool PostMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);
        [DllImport("user32.dll")]
        private static extern void mouse_event(uint dwFlags, uint dx, uint dy, uint dwData, UIntPtr dwExtraInfo);
        [DllImport("user32.dll")]
        private static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);
        [DllImport("user32.dll", CharSet = CharSet.Unicode)]
        private static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);
        [DllImport("user32.dll")]
        private static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);
        private delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
        [DllImport("user32.dll")]
        private static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);

        [StructLayout(LayoutKind.Sequential)]
        private struct RECT { public int Left, Top, Right, Bottom; }
        [StructLayout(LayoutKind.Sequential)]
        private struct POINT { public int X, Y; }

        public static string ResolveModRootDir()
        {
            string baseDir = AppDomain.CurrentDomain.BaseDirectory;
            if (string.IsNullOrEmpty(baseDir))
            {
                baseDir = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
            }
            DirectoryInfo di = new DirectoryInfo(baseDir);
            for (int i = 0; i < 4 && di != null; i++)
            {
                if (File.Exists(Path.Combine(di.FullName, "NroPort.exe")) ||
                    Directory.Exists(Path.Combine(di.FullName, "BepInEx")))
                {
                    return di.FullName;
                }
                di = di.Parent;
            }
            return baseDir;
        }

        public static string EnsureRelativeConfigAndQueueDir(string modRoot)
        {
            string queueDir = Path.Combine(modRoot, "tudzday-captcha");
            Directory.CreateDirectory(Path.Combine(queueDir, "inbox"));
            Directory.CreateDirectory(Path.Combine(queueDir, "jobs"));
            Directory.CreateDirectory(Path.Combine(queueDir, "outbox"));

            string cfgPath = Path.Combine(Path.Combine(modRoot, "BepInEx"), Path.Combine("config", "NroPort.Plugin.cfg"));
            if (File.Exists(cfgPath))
            {
                try
                {
                    string[] lines = File.ReadAllLines(cfgPath, Encoding.UTF8);
                    bool inCaptcha = false;
                    bool changed = false;
                    for (int i = 0; i < lines.Length; i++)
                    {
                        string trimmed = lines[i].Trim();
                        if (trimmed.StartsWith("[") && trimmed.EndsWith("]"))
                        {
                            inCaptcha = (string.Compare(trimmed, "[Captcha]", StringComparison.OrdinalIgnoreCase) == 0);
                        }
                        else if (inCaptcha)
                        {
                            if (trimmed.StartsWith("Enabled", StringComparison.OrdinalIgnoreCase))
                            {
                                if (lines[i] != "Enabled = true") { lines[i] = "Enabled = true"; changed = true; }
                            }
                            else if (trimmed.StartsWith("Mode", StringComparison.OrdinalIgnoreCase))
                            {
                                if (lines[i] != "Mode = ExternalQueue") { lines[i] = "Mode = ExternalQueue"; changed = true; }
                            }
                            else if (trimmed.StartsWith("QueueDir", StringComparison.OrdinalIgnoreCase))
                            {
                                string expected = "QueueDir = " + queueDir;
                                if (lines[i] != expected) { lines[i] = expected; changed = true; }
                            }
                        }
                    }
                    if (changed)
                    {
                        File.WriteAllLines(cfgPath, lines, Encoding.UTF8);
                    }
                }
                catch (Exception) { }
            }
            return queueDir;
        }

        public static void EnsureRelativeConfigAndStart()
        {
            lock (_lockObj)
            {
                if (_started) return;
                _started = true;
            }
            try
            {
                int myPid = Process.GetCurrentProcess().Id;
                Process[] others = Process.GetProcessesByName("AutoCaptcha");
                for (int i = 0; i < others.Length; i++)
                {
                    if (others[i].Id != myPid)
                    {
                        try { others[i].Kill(); } catch (Exception) { }
                    }
                }
            }
            catch (Exception) { }

            string modRoot = ResolveModRootDir();
            string queueDir = EnsureRelativeConfigAndQueueDir(modRoot);

            try
            {
                string helperExe = Path.Combine(modRoot, "AutoCaptcha.exe");
                if (File.Exists(helperExe))
                {
                    ProcessStartInfo psi = new ProcessStartInfo();
                    psi.FileName = helperExe;
                    psi.WorkingDirectory = modRoot;
                    psi.CreateNoWindow = true;
                    psi.UseShellExecute = false;
                    psi.WindowStyle = ProcessWindowStyle.Hidden;
                    Process.Start(psi);
                }
            }
            catch (Exception) { }

            Thread worker = new Thread(delegate()
            {
                RunWatchLoop(queueDir);
            });
            worker.IsBackground = true;
            worker.Name = "NroAutoCaptchaEmbeddedThread";
            worker.Start();
        }

        private static void InitBanks()
        {
            if (_uprightSymBank != null) return;

            _digitBank = new Dictionary<string, List<int[,]>>();
            foreach (KeyValuePair<string, string[]> kv in BUILTIN_DIGIT_BITMAPS)
            {
                int[,] mat = new int[16, 12];
                for (int r = 0; r < 16; r++)
                {
                    string rowStr = kv.Value[r];
                    for (int c = 0; c < 12; c++)
                    {
                        mat[r, c] = (rowStr[c] == '#') ? 1 : 0;
                    }
                }
                List<int[,]> list = new List<int[,]>();
                list.Add(mat);
                if (kv.Key == "1")
                {
                    int[,] oneNb = new int[16, 12];
                    for (int r = 0; r < 16; r++)
                    {
                        int srcR = (r >= 12) ? 6 : r;
                        for (int c = 0; c < 12; c++) oneNb[r, c] = mat[srcR, c];
                    }
                    list.Add(oneNb);
                }
                _digitBank[kv.Key] = list;
            }

            _uprightSymBank = new Dictionary<string, List<int[,]>>();
            _rotatedSymBank = new Dictionary<string, List<int[,]>>();

            byte[] compBytes = Convert.FromBase64String(PACKED_TEMPLATES_B64);
            string rawText;
            using (MemoryStream ms = new MemoryStream(compBytes))
            using (DeflateStream ds = new DeflateStream(ms, CompressionMode.Decompress))
            using (StreamReader sr = new StreamReader(ds, Encoding.UTF8))
            {
                rawText = sr.ReadToEnd();
            }

            string[] lines = rawText.Split(new char[] { '\n', '\r' }, StringSplitOptions.RemoveEmptyEntries);
            for (int i = 0; i < lines.Length; i++)
            {
                string[] parts = lines[i].Split('|');
                if (parts.Length < 3) continue;
                string bankType = parts[0];
                string chKey = parts[1];
                string[] tmpls = parts[2].Split(new char[] { ';' }, StringSplitOptions.RemoveEmptyEntries);
                List<int[,]> matList = new List<int[,]>(tmpls.Length);
                for (int t = 0; t < tmpls.Length; t++)
                {
                    string[] rowVals = tmpls[t].Split(',');
                    if (rowVals.Length < 16) continue;
                    int[,] mat = new int[16, 16];
                    for (int r = 0; r < 16; r++)
                    {
                        int v = int.Parse(rowVals[r], CultureInfo.InvariantCulture);
                        for (int c = 0; c < 16; c++)
                        {
                            mat[r, c] = (v >> (15 - c)) & 1;
                        }
                    }
                    matList.Add(mat);
                }
                if (bankType == "u") _uprightSymBank[chKey] = matList;
                else _rotatedSymBank[chKey] = matList;
            }
        }

        private static uint ReadUInt32BE(byte[] data, int offset)
        {
            return ((uint)data[offset] << 24) | ((uint)data[offset + 1] << 16) | ((uint)data[offset + 2] << 8) | data[offset + 3];
        }

        public static byte[,,] DecodePngPure(string filePath, out int height, out int width)
        {
            return DecodePngBytesPure(File.ReadAllBytes(filePath), out height, out width);
        }

        public static byte[,,] DecodePngBytesPure(byte[] data, out int height, out int width)
        {
            if (data.Length < 33 || data[0] != 137 || data[1] != 80 || data[2] != 78 || data[3] != 71)
                throw new InvalidDataException("Not a valid PNG file");

            int pos = 8;
            width = 0;
            height = 0;
            int bitDepth = 8;
            int colorType = 2;
            byte[][] palette = null;

            using (MemoryStream idatStream = new MemoryStream())
            {
                while (pos + 8 <= data.Length)
                {
                    int length = (int)ReadUInt32BE(data, pos);
                    string ctype = Encoding.ASCII.GetString(data, pos + 4, 4);
                    int cdataPos = pos + 8;
                    if (cdataPos + length > data.Length) break;

                    if (ctype == "IHDR")
                    {
                        width = (int)ReadUInt32BE(data, cdataPos);
                        height = (int)ReadUInt32BE(data, cdataPos + 4);
                        bitDepth = data[cdataPos + 8];
                        colorType = data[cdataPos + 9];
                    }
                    else if (ctype == "PLTE")
                    {
                        int n = length / 3;
                        palette = new byte[n][];
                        for (int i = 0; i < n; i++)
                        {
                            palette[i] = new byte[] { data[cdataPos + i * 3], data[cdataPos + i * 3 + 1], data[cdataPos + i * 3 + 2] };
                        }
                    }
                    else if (ctype == "IDAT")
                    {
                        idatStream.Write(data, cdataPos, length);
                    }
                    else if (ctype == "IEND")
                    {
                        break;
                    }
                    pos = cdataPos + length + 4;
                }

                byte[] idatBytes = idatStream.ToArray();
                if (idatBytes.Length <= 6) throw new InvalidDataException("Empty IDAT");

                int bpp;
                if (colorType == 2) bpp = 3;
                else if (colorType == 6) bpp = 4;
                else if (colorType == 0) bpp = 1;
                else if (colorType == 4) bpp = 2;
                else if (colorType == 3) bpp = 1;
                else throw new InvalidDataException("Unsupported colorType " + colorType);

                int stride = width * bpp;
                byte[] raw = new byte[height * (1 + stride)];

                // Skip 2-byte zlib header (78 9C / 78 01 / 78 DA)
                using (MemoryStream ms = new MemoryStream(idatBytes, 2, idatBytes.Length - 6))
                using (DeflateStream ds = new DeflateStream(ms, CompressionMode.Decompress))
                {
                    int totalRead = 0;
                    while (totalRead < raw.Length)
                    {
                        int n = ds.Read(raw, totalRead, raw.Length - totalRead);
                        if (n <= 0) break;
                        totalRead += n;
                    }
                }

                byte[,,] rgb = new byte[height, width, 3];
                byte[] prev = new byte[stride];
                byte[] cur = new byte[stride];
                int idx = 0;

                for (int y = 0; y < height; y++)
                {
                    int fType = raw[idx++];
                    for (int i = 0; i < stride; i++) cur[i] = raw[idx++];

                    if (fType == 1)
                    {
                        for (int i = bpp; i < stride; i++) cur[i] = (byte)((cur[i] + cur[i - bpp]) & 0xFF);
                    }
                    else if (fType == 2)
                    {
                        for (int i = 0; i < stride; i++) cur[i] = (byte)((cur[i] + prev[i]) & 0xFF);
                    }
                    else if (fType == 3)
                    {
                        for (int i = 0; i < bpp; i++) cur[i] = (byte)((cur[i] + (prev[i] >> 1)) & 0xFF);
                        for (int i = bpp; i < stride; i++) cur[i] = (byte)((cur[i] + ((cur[i - bpp] + prev[i]) >> 1)) & 0xFF);
                    }
                    else if (fType == 4)
                    {
                        for (int i = 0; i < bpp; i++) cur[i] = (byte)((cur[i] + prev[i]) & 0xFF);
                        for (int i = bpp; i < stride; i++)
                        {
                            int a = cur[i - bpp];
                            int b = prev[i];
                            int c = prev[i - bpp];
                            int p = a + b - c;
                            int pa = Math.Abs(p - a);
                            int pb = Math.Abs(p - b);
                            int pc = Math.Abs(p - c);
                            int pr = (pa <= pb && pa <= pc) ? a : ((pb <= pc) ? b : c);
                            cur[i] = (byte)((cur[i] + pr) & 0xFF);
                        }
                    }

                    if (colorType == 2)
                    {
                        for (int x = 0; x < width; x++)
                        {
                            int o = x * 3;
                            rgb[y, x, 0] = cur[o];
                            rgb[y, x, 1] = cur[o + 1];
                            rgb[y, x, 2] = cur[o + 2];
                        }
                    }
                    else if (colorType == 6)
                    {
                        for (int x = 0; x < width; x++)
                        {
                            int o = x * 4;
                            rgb[y, x, 0] = cur[o];
                            rgb[y, x, 1] = cur[o + 1];
                            rgb[y, x, 2] = cur[o + 2];
                        }
                    }
                    else if (colorType == 3 && palette != null)
                    {
                        for (int x = 0; x < width; x++)
                        {
                            byte[] p = palette[cur[x]];
                            rgb[y, x, 0] = p[0];
                            rgb[y, x, 1] = p[1];
                            rgb[y, x, 2] = p[2];
                        }
                    }
                    else
                    {
                        for (int x = 0; x < width; x++)
                        {
                            byte v = cur[x * bpp];
                            rgb[y, x, 0] = v; rgb[y, x, 1] = v; rgb[y, x, 2] = v;
                        }
                    }
                    Buffer.BlockCopy(cur, 0, prev, 0, stride);
                }
                return rgb;
            }
        }

        private static int[,] DilateRect(int[,] mask, int kw, int kh)
        {
            int h = mask.GetLength(0);
            int w = mask.GetLength(1);
            int padL = (kw - 1) / 2, padR = kw / 2;
            int padT = (kh - 1) / 2, padB = kh / 2;
            int[,] horiz = new int[h, w];
            for (int y = 0; y < h; y++)
            {
                for (int x = 0; x < w; x++)
                {
                    int x0 = Math.Max(0, x - padL), x1 = Math.Min(w, x + padR + 1);
                    for (int ix = x0; ix < x1; ix++)
                    {
                        if (mask[y, ix] != 0) { horiz[y, x] = 1; break; }
                    }
                }
            }
            if (kh <= 1) return horiz;
            int[,] outM = new int[h, w];
            for (int y = 0; y < h; y++)
            {
                int y0 = Math.Max(0, y - padT), y1 = Math.Min(h, y + padB + 1);
                for (int x = 0; x < w; x++)
                {
                    for (int iy = y0; iy < y1; iy++)
                    {
                        if (horiz[iy, x] != 0) { outM[y, x] = 1; break; }
                    }
                }
            }
            return outM;
        }

        private static int[,] ErodeRect(int[,] mask, int kw, int kh)
        {
            int h = mask.GetLength(0);
            int w = mask.GetLength(1);
            int padL = (kw - 1) / 2, padR = kw / 2;
            int padT = (kh - 1) / 2, padB = kh / 2;
            int[,] horiz = new int[h, w];
            for (int y = 0; y < h; y++)
            {
                for (int x = 0; x < w; x++)
                {
                    if (x - padL < 0 || x + padR >= w) continue;
                    bool ok = true;
                    for (int ix = x - padL; ix <= x + padR; ix++)
                    {
                        if (mask[y, ix] == 0) { ok = false; break; }
                    }
                    if (ok) horiz[y, x] = 1;
                }
            }
            if (kh <= 1) return horiz;
            int[,] outM = new int[h, w];
            for (int y = 0; y < h; y++)
            {
                if (y - padT < 0 || y + padB >= h) continue;
                for (int x = 0; x < w; x++)
                {
                    bool ok = true;
                    for (int iy = y - padT; iy <= y + padB; iy++)
                    {
                        if (horiz[iy, x] == 0) { ok = false; break; }
                    }
                    if (ok) outM[y, x] = 1;
                }
            }
            return outM;
        }

        private static int[,] MorphOpen(int[,] mask, int kw, int kh) { return DilateRect(ErodeRect(mask, kw, kh), kw, kh); }
        private static int[,] MorphClose(int[,] mask, int kw, int kh) { return ErodeRect(DilateRect(mask, kw, kh), kw, kh); }

        private static List<CompItem> ConnectedComponents(int[,] mask)
        {
            int h = mask.GetLength(0);
            int w = mask.GetLength(1);
            bool[,] vis = new bool[h, w];
            List<CompItem> comps = new List<CompItem>();
            int[] dyArr = new int[] { -1, -1, -1, 0, 0, 1, 1, 1 };
            int[] dxArr = new int[] { -1, 0, 1, -1, 1, -1, 0, 1 };

            for (int y = 0; y < h; y++)
            {
                for (int x = 0; x < w; x++)
                {
                    if (mask[y, x] != 0 && !vis[y, x])
                    {
                        vis[y, x] = true;
                        Queue<int[]> q = new Queue<int[]>();
                        q.Enqueue(new int[] { y, x });
                        List<int[]> pix = new List<int[]>();
                        int minX = x, maxX = x, minY = y, maxY = y;
                        long sumX = 0;

                        while (q.Count > 0)
                        {
                            int[] cur = q.Dequeue();
                            int cy = cur[0], cx = cur[1];
                            pix.Add(cur);
                            if (cx < minX) minX = cx;
                            if (cx > maxX) maxX = cx;
                            if (cy < minY) minY = cy;
                            if (cy > maxY) maxY = cy;
                            sumX += cx;

                            for (int d = 0; d < 8; d++)
                            {
                                int ny = cy + dyArr[d], nx = cx + dxArr[d];
                                if (ny >= 0 && ny < h && nx >= 0 && nx < w && mask[ny, nx] != 0 && !vis[ny, nx])
                                {
                                    vis[ny, nx] = true;
                                    q.Enqueue(new int[] { ny, nx });
                                }
                            }
                        }
                        CompItem ci = new CompItem();
                        ci.X = minX; ci.Y = minY;
                        ci.W = maxX - minX + 1; ci.H = maxY - minY + 1;
                        ci.Area = pix.Count;
                        ci.XMean = (double)sumX / pix.Count;
                        ci.Pixels = pix;
                        comps.Add(ci);
                    }
                }
            }
            return comps;
        }

        private static int[,] Crop2D(int[,] mask, int y0, int y1, int x0, int x1)
        {
            int H = mask.GetLength(0), W = mask.GetLength(1);
            y0 = Math.Max(0, Math.Min(H, y0));
            y1 = Math.Max(y0, Math.Min(H, y1));
            x0 = Math.Max(0, Math.Min(W, x0));
            x1 = Math.Max(x0, Math.Min(W, x1));
            int ch = y1 - y0, cw = x1 - x0;
            int[,] res = new int[ch, cw];
            for (int y = 0; y < ch; y++)
                for (int x = 0; x < cw; x++)
                    res[y, x] = mask[y0 + y, x0 + x];
            return res;
        }

        private static bool TightBbox(int[,] mask, out int y0, out int y1, out int x0, out int x1)
        {
            int h = mask.GetLength(0), w = mask.GetLength(1);
            y0 = h; y1 = -1; x0 = w; x1 = -1;
            for (int y = 0; y < h; y++)
            {
                for (int x = 0; x < w; x++)
                {
                    if (mask[y, x] != 0)
                    {
                        if (y < y0) y0 = y;
                        if (y > y1) y1 = y;
                        if (x < x0) x0 = x;
                        if (x > x1) x1 = x;
                    }
                }
            }
            if (y1 < 0) return false;
            y1 += 1; x1 += 1;
            return true;
        }

        private static int[,] ResizeAreaBinary(int[,] mask, int outW, int outH, double threshold)
        {
            int inH = mask.GetLength(0), inW = mask.GetLength(1);
            int[,] res = new int[outH, outW];
            if (inH == 0 || inW == 0) return res;

            for (int oy = 0; oy < outH; oy++)
            {
                double sy0 = (double)oy * inH / outH;
                double sy1 = (double)(oy + 1) * inH / outH;
                int iy0 = (int)Math.Floor(sy0);
                int iy1 = Math.Min(inH, (int)Math.Ceiling(sy1));
                for (int ox = 0; ox < outW; ox++)
                {
                    double sx0 = (double)ox * inW / outW;
                    double sx1 = (double)(ox + 1) * inW / outW;
                    int ix0 = (int)Math.Floor(sx0);
                    int ix1 = Math.Min(inW, (int)Math.Ceiling(sx1));
                    double totalW = 0.0, acc = 0.0;
                    for (int iy = iy0; iy < iy1; iy++)
                    {
                        double wy = Math.Min(sy1, iy + 1.0) - Math.Max(sy0, (double)iy);
                        if (wy <= 0) continue;
                        for (int ix = ix0; ix < ix1; ix++)
                        {
                            double wx = Math.Min(sx1, ix + 1.0) - Math.Max(sx0, (double)ix);
                            if (wx <= 0) continue;
                            double w = wy * wx;
                            totalW += w;
                            if (mask[iy, ix] != 0) acc += w;
                        }
                    }
                    if (totalW > 0 && (acc / totalW) > threshold) res[oy, ox] = 1;
                }
            }
            return res;
        }

        private static int[,] NormalizeSymbol16(int[,] cropMask)
        {
            int y0, y1, x0, x1;
            if (!TightBbox(cropMask, out y0, out y1, out x0, out x1)) return new int[16, 16];
            int[,] sub = Crop2D(cropMask, y0, y1, x0, x1);
            int h = sub.GetLength(0), w = sub.GetLength(1);
            if (h == 0 || w == 0) return new int[16, 16];

            double scale = 14.0 / Math.Max(h, w);
            int nw = Math.Max(1, Math.Min(16, (int)Math.Round(w * scale)));
            int nh = Math.Max(1, Math.Min(16, (int)Math.Round(h * scale)));
            int[,] resized = ResizeAreaBinary(sub, nw, nh, 0.32);
            int[,] canvas = new int[16, 16];
            int px = (16 - nw) / 2, py = (16 - nh) / 2;
            for (int r = 0; r < nh; r++)
                for (int c = 0; c < nw; c++)
                    canvas[py + r, px + c] = resized[r, c];
            return canvas;
        }

        private static double ScoreBinary2D(int[,] a, int[,] b)
        {
            int H = a.GetLength(0), W = a.GetLength(1);
            int n = H * W;
            int sumA = 0, sumB = 0, sumAB = 0;
            for (int r = 0; r < H; r++)
            {
                for (int c = 0; c < W; c++)
                {
                    int va = a[r, c], vb = b[r, c];
                    sumA += va; sumB += vb;
                    if (va != 0 && vb != 0) sumAB += 1;
                }
            }
            if (sumA == 0 || sumB == 0) return 0.0;
            double meanA = (double)sumA / n;
            double meanB = (double)sumB / n;
            double num = sumAB - n * meanA * meanB;
            double varA = sumA - n * meanA * meanA;
            double varB = sumB - n * meanB * meanB;
            double den = Math.Sqrt(Math.Max(0.0, varA * varB)) + 1e-6;
            return num / den;
        }

        private static Dictionary<string, int[,]> BuildColorMasksPure(byte[,,] rgb, int yOffset, int hSlice, int W)
        {
            Dictionary<string, int[,]> masks = new Dictionary<string, int[,]>();
            for (int i = 0; i < ORDER.Length; i++) masks[ORDER[i]] = new int[hSlice, W];

            for (int y = 0; y < hSlice; y++)
            {
                int sy = yOffset + y;
                for (int x = 0; x < W; x++)
                {
                    int r = rgb[sy, x, 0], g = rgb[sy, x, 1], b = rgb[sy, x, 2];
                    int mx = Math.Max(r, Math.Max(g, b));
                    int mn = Math.Min(r, Math.Min(g, b));
                    int diff = mx - mn;

                    if (r > 165 && g > 165 && b > 165 && diff < 55) masks["W"][y, x] = 1;
                    if (r > 165 && g > 145 && b < 115 && (r - b) > 65) masks["Y"][y, x] = 1;
                    if (r > 145 && b > 145 && g < 120 && (r - g) > 45 && (b - g) > 45) masks["M"][y, x] = 1;
                    if (g > 145 && r < 120 && b < 120 && (g - r) > 45 && (g - b) > 45) masks["G"][y, x] = 1;
                    if (b > 150 && r < 115 && (b - r) > 55 && (b - g) > 25) masks["B"][y, x] = 1;
                    if (r > 155 && g < 105 && b < 105 && (r - g) > 60 && (r - b) > 60) masks["R"][y, x] = 1;
                    if (mx < 52 && diff < 28) masks["K"][y, x] = 1;
                }
            }
            return masks;
        }

        private static int[,] RemoveHorizontalLinesPure(byte[,,] rgb, int yTop, int W, int window)
        {
            int half = window / 2;
            int[,] fgLoc = new int[yTop, W];
            List<int> rVals = new List<int>(window);
            List<int> gVals = new List<int>(window);
            List<int> bVals = new List<int>(window);

            for (int y = 0; y < yTop; y++)
            {
                for (int x = 0; x < W; x++)
                {
                    int x0 = Math.Max(0, x - half);
                    int x1 = Math.Min(W, x + half + 1);
                    rVals.Clear(); gVals.Clear(); bVals.Clear();
                    for (int nx = x0; nx < x1; nx += 2)
                    {
                        rVals.Add(rgb[y, nx, 0]);
                        gVals.Add(rgb[y, nx, 1]);
                        bVals.Add(rgb[y, nx, 2]);
                    }
                    rVals.Sort(); gVals.Sort(); bVals.Sort();
                    int mid = rVals.Count / 2;
                    int medR = rVals[mid], medG = gVals[mid], medB = bVals[mid];
                    int r = rgb[y, x, 0], g = rgb[y, x, 1], b = rgb[y, x, 2];
                    int diff = Math.Abs(r - medR) + Math.Abs(g - medG) + Math.Abs(b - medB);
                    int mx = Math.Max(r, Math.Max(g, b));
                    int mn = Math.Min(r, Math.Min(g, b));
                    if (diff > 42 && (mx > 62 || (mx < 52 && (mx - mn) < 28)))
                    {
                        fgLoc[y, x] = 1;
                    }
                }
            }
            return fgLoc;
        }

        private static Dictionary<string, double> ScoreAllOddDigits(int[,] cropMask)
        {
            Dictionary<string, double> scores = new Dictionary<string, double>();
            int y0, y1, x0, x1;
            if (!TightBbox(cropMask, out y0, out y1, out x0, out x1))
            {
                for (int i = 0; i < ODD_DIGITS.Length; i++) scores[ODD_DIGITS[i]] = 0.0;
                return scores;
            }
            int[,] sub = Crop2D(cropMask, y0, y1, x0, x1);
            int[,] norm = ResizeAreaBinary(sub, 12, 16, 0.33);

            for (int i = 0; i < ODD_DIGITS.Length; i++)
            {
                string d = ODD_DIGITS[i];
                double bestS = -1.0;
                List<int[,]> tmpls = _digitBank[d];
                for (int t = 0; t < tmpls.Count; t++)
                {
                    int[,] tmpl = tmpls[t];
                    int inter = 0, union = 0;
                    for (int r = 0; r < 16; r++)
                    {
                        for (int c = 0; c < 12; c++)
                        {
                            int va = norm[r, c], vb = tmpl[r, c];
                            if (va != 0 && vb != 0) inter++;
                            if (va != 0 || vb != 0) union++;
                        }
                    }
                    double iou = inter / (union + 1e-5);
                    double ncc = ScoreBinary2D(norm, tmpl);
                    double sc = 0.55 * iou + 0.45 * ncc;
                    if (sc > bestS) bestS = sc;
                }
                scores[d] = bestS;
            }
            return scores;
        }

        private static string ClassifyLegendSymbol(int[,] symCrop, out double outScore, out Dictionary<string, double> outAllSymScores)
        {
            outScore = 0.0;
            outAllSymScores = new Dictionary<string, double>();
            int y0, y1, x0, x1;
            if (!TightBbox(symCrop, out y0, out y1, out x0, out x1)) return "?";
            symCrop = Crop2D(symCrop, y0, y1, x0, x1);

            int h0 = symCrop.GetLength(0), w0 = symCrop.GetLength(1);
            List<int> validR = new List<int>();
            for (int r = 0; r < h0; r++)
            {
                int rowSum = 0;
                for (int c = 0; c < w0; c++) rowSum += symCrop[r, c];
                if (rowSum > 2) validR.Add(r);
            }
            if (validR.Count >= 10)
            {
                symCrop = Crop2D(symCrop, validR[0], validR[validR.Count - 1] + 1, 0, w0);
            }

            int h = symCrop.GetLength(0), w = symCrop.GetLength(1);
            if (w > 14 && h <= 17 && h >= 5)
            {
                int topR5 = 0;
                for (int r = 0; r < 5; r++)
                    for (int c = 14; c < w; c++) topR5 += symCrop[r, c];
                if (topR5 == 0)
                    symCrop = Crop2D(symCrop, 0, h, 0, 14);
            }
            else if (w > 15 && h >= 8)
            {
                int topR = 0, botR = 0;
                for (int r = 0; r < 4; r++)
                    for (int c = 15; c < w; c++) topR += symCrop[r, c];
                for (int r = h - 4; r < h; r++)
                    for (int c = 15; c < w; c++) botR += symCrop[r, c];
                if (topR == 0 && botR == 0)
                    symCrop = Crop2D(symCrop, 0, h, 0, 15);
            }
            h = symCrop.GetLength(0);
            w = symCrop.GetLength(1);
            if (h >= 17 && w > 10)
            {
                int maxCut = Math.Min(15, w);
                for (int xCut = 5; xCut < maxCut; xCut++)
                {
                    int topL = 0, botL = 0, topR = 0, botR = 0;
                    for (int r = 0; r < 5; r++)
                    {
                        for (int c = 0; c < xCut; c++) topL += symCrop[r, c];
                        for (int c = xCut; c < w; c++) topR += symCrop[r, c];
                    }
                    for (int r = h - 5; r < h; r++)
                    {
                        for (int c = 0; c < xCut; c++) botL += symCrop[r, c];
                        for (int c = xCut; c < w; c++) botR += symCrop[r, c];
                    }
                    if (topL >= 4 && botL >= 4 && topR == 0 && botR == 0)
                    {
                        symCrop = Crop2D(symCrop, 0, h, 0, xCut);
                        break;
                    }
                }
            }
            h = symCrop.GetLength(0);
            w = symCrop.GetLength(1);
            if (h >= 12 && w >= 19)
            {
                while (symCrop.GetLength(1) > 16)
                {
                    int cSum = 0, top8 = 0;
                    for (int r = 0; r < h; r++) cSum += symCrop[r, 0];
                    for (int r = 0; r < 8; r++) top8 += symCrop[r, 0];
                    if (cSum <= 6 && top8 == 0) symCrop = Crop2D(symCrop, 0, h, 1, symCrop.GetLength(1));
                    else break;
                }
                while (symCrop.GetLength(1) > 16)
                {
                    int lastC = symCrop.GetLength(1) - 1;
                    int cSum = 0, top8 = 0, botRest = 0;
                    for (int r = 0; r < h; r++) cSum += symCrop[r, lastC];
                    for (int r = 0; r < 8; r++) top8 += symCrop[r, lastC];
                    for (int r = 3; r < h; r++) botRest += symCrop[r, lastC];
                    if ((cSum <= 4 && top8 == 0) || botRest == 0) symCrop = Crop2D(symCrop, 0, h, 0, lastC);
                    else break;
                }
            }
            if (TightBbox(symCrop, out y0, out y1, out x0, out x1))
                symCrop = Crop2D(symCrop, y0, y1, x0, x1);

            h = symCrop.GetLength(0);
            w = symCrop.GetLength(1);
            if (w <= 6 && h >= 14)
            {
                outScore = 0.92;
                outAllSymScores["L"] = 0.92;
                outAllSymScores["I"] = 0.90;
                return "L";
            }
            int[,] norm = NormalizeSymbol16(symCrop);

            List<string> pool = new List<string>();
            if (w >= 19)
            {
                pool.AddRange(new string[] { "@", "%", "W", "M", "w", "m", "&" });
            }
            else if (h <= 16)
            {
                for (int i = 0; i < XHEIGHT_LOWER.Length; i++)
                {
                    string ch = XHEIGHT_LOWER[i].ToString();
                    if (ch != "m" && ch != "w") pool.Add(ch);
                }
                pool.Add("#"); pool.Add("$");
            }
            else
            {
                for (int i = 0; i < TALL_CHARS.Length; i++)
                {
                    string ch = TALL_CHARS[i].ToString();
                    if (ch != "M" && ch != "W" && ch != "@" && ch != "%") pool.Add(ch);
                }
            }

            if (h <= 16 && w >= 12 && w <= 16 && h >= 5)
            {
                int bRows = 5;
                double[] colFill = new double[w];
                for (int c = 0; c < w; c++)
                {
                    int s = 0;
                    for (int r = h - bRows; r < h; r++) s += symCrop[r, c];
                    colFill[c] = (double)s / bRows;
                }
                int c1 = w / 3;
                int c2 = Math.Max(c1 + 1, (2 * w) / 3);
                double midMin = 1.0, leftLeg = 0.0, rightLeg = 0.0;
                for (int c = c1; c < c2; c++) if (colFill[c] < midMin) midMin = colFill[c];
                for (int c = 0; c < c1; c++) if (colFill[c] > leftLeg) leftLeg = colFill[c];
                for (int c = c2; c < w; c++) if (colFill[c] > rightLeg) rightLeg = colFill[c];

                if (leftLeg > 0.80 && rightLeg > 0.80 && midMin < 0.25)
                {
                    List<string> filtered = new List<string>();
                    for (int i = 0; i < pool.Count; i++)
                    {
                        string p = pool[i];
                        if (p == "n" || p == "u" || p == "h" || p == "r" || p == "v" || p == "x") filtered.Add(p);
                    }
                    pool = filtered;
                }
            }

            int botRightSum = 0;
            for (int r = 11; r < 15; r++)
                for (int c = 11; c < 15; c++) botRightSum += norm[r, c];
            bool botRightEmpty = (botRightSum == 0);

            int sumMLeg = 0, sumMReg = 0, sumBellyL = 0, sumBotC = 0;
            for (int r = 5; r < 9; r++)
            {
                for (int c = 1; c < 5; c++) sumMLeg += norm[r, c];
                for (int c = 9; c < 13; c++) sumMReg += norm[r, c];
            }
            for (int r = 10; r < 14; r++)
                for (int c = 1; c < 5; c++) sumBellyL += norm[r, c];
            for (int r = 13; r < 15; r++)
                for (int c = 5; c < 10; c++) sumBotC += norm[r, c];
            double midLeft = sumMLeg / 16.0;
            double midRight = sumMReg / 16.0;
            double bellyLeft = sumBellyL / 16.0;
            double botCenter = sumBotC / 10.0;
            int sumTC = 0;
            for (int r = 0; r < 4; r++)
                for (int c = 5; c < 11; c++) sumTC += norm[r, c];
            double topCenter = sumTC / 24.0;

            string bestCh = "?";
            double bestS = -1.0;
            for (int i = 0; i < pool.Count; i++)
            {
                string ch = pool[i];
                List<int[,]> tmpls;
                if (!_uprightSymBank.TryGetValue(ch, out tmpls)) continue;
                for (int t = 0; t < tmpls.Count; t++)
                {
                    double s = ScoreBinary2D(norm, tmpls[t]);
                    if (ch == "@" && botRightEmpty) s += 0.15;
                    if (string.Compare(ch, "a", StringComparison.OrdinalIgnoreCase) == 0 && midLeft < 0.20 && bellyLeft < 0.20) s -= 0.25;
                    if (string.Compare(ch, "s", StringComparison.OrdinalIgnoreCase) == 0)
                    {
                        if (midLeft < 0.20 && midRight > 0.60 && bellyLeft < 0.25) s += 0.10;
                        else if (bellyLeft >= 0.45 && midRight >= 0.40) s -= 0.12;
                    }
                    if (ch == "Q" && h >= 20 && !botRightEmpty && midRight >= 0.35) s += 0.12;
                    if (string.Compare(ch, "c", StringComparison.OrdinalIgnoreCase) == 0 && midRight < 0.15 && midLeft >= 0.50) s += 0.12;
                    if (ch == "&" && bellyLeft >= 0.45 && midRight >= 0.40) s += 0.10;
                    if (string.Compare(ch, "b", StringComparison.OrdinalIgnoreCase) == 0)
                    {
                        if (topCenter < 0.25 && botCenter >= 0.50) s -= 0.15;
                        else if (botCenter >= 0.60) s += 0.08;
                    }
                    if (string.Compare(ch, "u", StringComparison.OrdinalIgnoreCase) == 0 && topCenter < 0.25 && botCenter >= 0.50)
                        s += 0.12;
                    string upKey = ch.ToUpperInvariant();
                    double prevBest;
                    if (!outAllSymScores.TryGetValue(upKey, out prevBest) || s > prevBest)
                        outAllSymScores[upKey] = s;
                    if (s > bestS)
                    {
                        bestS = s;
                        bestCh = ch;
                    }
                }
            }
            outScore = Math.Round(bestS, 3);
            return bestCh.ToUpperInvariant();
        }

        private static List<LegendEntry> ExtractLegendEntries(byte[,,] rgb, int H, int W)
        {
            int y0Bot = (int)Math.Round(H * 135.0 / 256.0);
            int y1Bot = (int)Math.Round(H * 230.0 / 256.0);
            int hSlice = y1Bot - y0Bot;

            Dictionary<string, int[,]> rawMasks = BuildColorMasksPure(rgb, y0Bot, hSlice, W);
            Dictionary<string, int[,]> openMasks = new Dictionary<string, int[,]>();
            Dictionary<string, int[,]> closeMasks = new Dictionary<string, int[,]>();
            for (int i = 0; i < ORDER.Length; i++)
            {
                string name = ORDER[i];
                openMasks[name] = MorphOpen(rawMasks[name], 1, 3);
                closeMasks[name] = MorphClose(openMasks[name], 2, 6);
            }

            int[][] cellDefs = new int[][] {
                new int[] { 5, 33, 16, Math.Min(96, W) },
                new int[] { 32, 60, 16, Math.Min(96, W) },
                new int[] { 58, 88, 16, Math.Min(96, W) },
                new int[] { 5, 33, 146, Math.Min(244, W) },
                new int[] { 32, 60, 146, Math.Min(244, W) }
            };
            string[] cellNames = new string[] { "L1", "L2", "L3", "R1", "R2" };

            HashSet<string> usedColors = new HashSet<string>();
            List<LegendEntry> entries = new List<LegendEntry>();

            for (int ci = 0; ci < cellDefs.Length; ci++)
            {
                int cy0 = cellDefs[ci][0], cy1 = cellDefs[ci][1], cx0 = cellDefs[ci][2], cx1 = cellDefs[ci][3];
                string bestColor = null;
                int bestCnt = 0;
                for (int i = 0; i < ORDER.Length; i++)
                {
                    string name = ORDER[i];
                    if (usedColors.Contains(name)) continue;
                    int[,] sub = Crop2D(openMasks[name], cy0, cy1, cx0, cx1);
                    int cnt = 0;
                    for (int r = 0; r < sub.GetLength(0); r++)
                        for (int c = 0; c < sub.GetLength(1); c++) cnt += sub[r, c];
                    if (cnt > bestCnt) { bestCnt = cnt; bestColor = name; }
                }
                if (bestColor == null || bestCnt < 80) continue;
                usedColors.Add(bestColor);

                int[,] cellOpen = Crop2D(openMasks[bestColor], cy0, cy1, cx0, cx1);
                int[,] cellClose = Crop2D(closeMasks[bestColor], cy0, cy1, cx0, cx1);
                int ch = cellOpen.GetLength(0), cw = cellOpen.GetLength(1);

                List<CompItem> preComps = ConnectedComponents(cellOpen);
                for (int pc = 0; pc < preComps.Count; pc++)
                {
                    CompItem cItem = preComps[pc];
                    if (cItem.Area < 12 || (cItem.W <= 2 && cItem.Area < 18) || (cItem.X == 0 && cItem.W >= 12 && cItem.H <= 9))
                    {
                        for (int p = 0; p < cItem.Pixels.Count; p++)
                            cellOpen[cItem.Pixels[p][0], cItem.Pixels[p][1]] = 0;
                    }
                }

                int symX0 = 0;
                for (int x = 0; x < cw; x++)
                {
                    int colSum = 0;
                    for (int y = 0; y < ch; y++) colSum += cellOpen[y, x];
                    if (colSum >= 2) { symX0 = x; break; }
                }

                int digX0 = Math.Min(cw - 8, symX0 + 35);
                int[,] rightHalf = Crop2D(cellClose, 0, ch, digX0, cw);
                List<CompItem> dComps = ConnectedComponents(rightHalf);
                CompItem bestDComp = null;
                int bestRightEdge = -1;
                for (int i = 0; i < dComps.Count; i++)
                {
                    CompItem c = dComps[i];
                    if (c.Area >= 25 && c.H >= 9 && c.W >= 4)
                    {
                        if (c.X + c.W > bestRightEdge) { bestRightEdge = c.X + c.W; bestDComp = c; }
                    }
                }
                int[,] digCrop = (bestDComp != null)
                    ? Crop2D(rightHalf, bestDComp.Y, bestDComp.Y + bestDComp.H, bestDComp.X, bestDComp.X + bestDComp.W)
                    : rightHalf;
                int dhC = digCrop.GetLength(0), dwC = digCrop.GetLength(1);
                if (dwC > 16 && dhC > 0)
                {
                    int[,] rightOpen = Crop2D(cellOpen, 0, ch, digX0, cw);
                    int[,] digOpen = (bestDComp != null)
                        ? Crop2D(rightOpen, bestDComp.Y, bestDComp.Y + bestDComp.H, bestDComp.X, bestDComp.X + bestDComp.W)
                        : rightOpen;
                    int[] colS = new int[dwC];
                    for (int c = 0; c < dwC; c++)
                        for (int r = 0; r < dhC; r++) colS[c] += digCrop[r, c];
                    int bestWx = 0, bestWSum = -1;
                    for (int wx = 0; wx <= dwC - 14; wx++)
                    {
                        int ws = 0;
                        for (int c = wx; c < wx + 14; c++) if (colS[c] >= 8) ws += colS[c];
                        if (ws > bestWSum) { bestWSum = ws; bestWx = wx; }
                    }
                    digCrop = Crop2D(digOpen, 0, dhC, bestWx, bestWx + 14);
                    for (int c = 0; c < digCrop.GetLength(1); c++)
                    {
                        int cs = 0;
                        for (int r = 0; r < dhC; r++) cs += digCrop[r, c];
                        if (cs <= 4) for (int r = 0; r < dhC; r++) digCrop[r, c] = 0;
                    }
                    int dy0, dy1, dx0, dx1;
                    if (TightBbox(digCrop, out dy0, out dy1, out dx0, out dx1))
                        digCrop = Crop2D(digCrop, dy0, dy1, dx0, dx1);
                }
                Dictionary<string, double> dScores = ScoreAllOddDigits(digCrop);
                if (dwC >= 40 && dScores.ContainsKey("5")) dScores["5"] += 0.06;

                int[,] symPartOpen = Crop2D(cellOpen, 0, ch, symX0, Math.Min(cw, symX0 + 24));
                List<CompItem> lComps = ConnectedComponents(symPartOpen);
                bool hasNarrowStem = false;
                for (int i = 0; i < lComps.Count; i++)
                {
                    if (lComps[i].X <= 3 && lComps[i].W <= 5 && lComps[i].H >= 15) hasNarrowStem = true;
                }
                for (int i = 0; i < lComps.Count; i++)
                {
                    CompItem lc = lComps[i];
                    if ((lc.X >= 13 && lc.H <= 8) || (hasNarrowStem && lc.X >= 5 && lc.H <= 6))
                    {
                        for (int p = 0; p < lc.Pixels.Count; p++)
                            symPartOpen[lc.Pixels[p][0], lc.Pixels[p][1]] = 0;
                    }
                }
                List<CompItem> sComps = ConnectedComponents(symPartOpen);
                int maxH = 0;
                for (int i = 0; i < sComps.Count; i++)
                    if (sComps[i].Area >= 15 && sComps[i].H > maxH) maxH = sComps[i].H;

                int[,] symPart = (maxH < 14) ? MorphClose(symPartOpen, 1, 4) : symPartOpen;
                double symScore;
                Dictionary<string, double> allSymSc;
                string symChar = ClassifyLegendSymbol(symPart, out symScore, out allSymSc);

                LegendEntry le = new LegendEntry();
                le.Cell = cellNames[ci];
                le.ColorName = bestColor;
                le.Symbol = symChar;
                le.Digit = "1";
                le.SymScore = symScore;
                le.AllDigScores = dScores;
                le.AllSymScores = allSymSc;
                entries.Add(le);
            }

            // Đảm bảo 5 dòng Legend có 5 ký hiệu hoàn toàn KHÁC NHAU (chống trùng lặp như B->3 và B->1)
            List<int> orderBySym = new List<int>();
            for (int i = 0; i < entries.Count; i++) orderBySym.Add(i);
            orderBySym.Sort(delegate(int a, int b) { return entries[b].SymScore.CompareTo(entries[a].SymScore); });
            HashSet<string> usedSyms = new HashSet<string>();
            for (int idx = 0; idx < orderBySym.Count; idx++)
            {
                LegendEntry le = entries[orderBySym[idx]];
                if (!usedSyms.Contains(le.Symbol))
                {
                    usedSyms.Add(le.Symbol);
                }
                else if (le.AllSymScores != null && le.AllSymScores.Count > 0)
                {
                    string bestAlt = le.Symbol;
                    double bestAltSc = -999.0;
                    foreach (KeyValuePair<string, double> kv in le.AllSymScores)
                    {
                        if (!usedSyms.Contains(kv.Key) && kv.Value > bestAltSc)
                        {
                            bestAltSc = kv.Value;
                            bestAlt = kv.Key;
                        }
                    }
                    le.Symbol = bestAlt;
                    le.SymScore = Math.Round(bestAltSc, 3);
                    usedSyms.Add(bestAlt);
                }
            }

            if (entries.Count >= 1 && entries.Count <= 5)
            {
                List<string[]> perms = new List<string[]>();
                GeneratePermutations(ODD_DIGITS, 0, entries.Count, new string[entries.Count], new bool[5], perms);
                double bestSum = -999.0;
                string[] bestPerm = perms[0];
                for (int p = 0; p < perms.Count; p++)
                {
                    double s = 0.0;
                    for (int i = 0; i < entries.Count; i++) s += entries[i].AllDigScores[perms[p][i]];
                    if (s > bestSum) { bestSum = s; bestPerm = perms[p]; }
                }
                for (int i = 0; i < entries.Count; i++)
                {
                    entries[i].Digit = bestPerm[i];
                    entries[i].DigScore = Math.Round(entries[i].AllDigScores[bestPerm[i]], 3);
                }
            }
            return entries;
        }

        private static void GeneratePermutations(string[] arr, int depth, int k, string[] cur, bool[] used, List<string[]> res)
        {
            if (depth == k)
            {
                string[] copy = new string[k];
                Array.Copy(cur, copy, k);
                res.Add(copy);
                return;
            }
            for (int i = 0; i < arr.Length; i++)
            {
                if (!used[i])
                {
                    used[i] = true;
                    cur[depth] = arr[i];
                    GeneratePermutations(arr, depth + 1, k, cur, used, res);
                    used[i] = false;
                }
            }
        }

        private static string ClassifyTopGlyph(int[,] subRaw, int[,] subLoc, List<string> allowedSymbols, out double outScore, out string outAltSym, out double outAltScore)
        {
            int[,] bRaw = MorphClose(subRaw, 2, 5);
            int hRaw = subRaw.GetLength(0), wRaw = subRaw.GetLength(1);
            int[,] subClean = new int[hRaw, wRaw];
            for (int r = 0; r < hRaw; r++)
            {
                int rSum = 0;
                for (int c = 0; c < wRaw; c++) rSum += subRaw[r, c];
                bool clearRow = (wRaw >= 34 && rSum >= (int)(0.92 * wRaw));
                for (int c = 0; c < wRaw; c++) subClean[r, c] = clearRow ? 0 : subRaw[r, c];
            }
            int[,] opened = MorphOpen(subClean, 1, 3);
            int[,] bOpen = MorphClose(opened, 2, 6);
            int[,] bLoc = MorphClose((subLoc != null) ? subLoc : opened, 2, 6);

            int[,] normRaw = NormalizeSymbol16(bRaw);
            int[,] normOpen = NormalizeSymbol16(bOpen);
            int[,] normLoc = NormalizeSymbol16(bLoc);

            int sumML = 0, sumMR = 0, sumUML = 0, sumCR = 0;
            for (int r = 5; r < 12; r++)
            {
                for (int c = 1; c < 6; c++) sumML += normOpen[r, c];
                for (int c = 10; c < 15; c++) sumMR += normOpen[r, c];
            }
            for (int r = 4; r < 7; r++)
                for (int c = 1; c < 6; c++) sumUML += normOpen[r, c];
            for (int r = 6; r < 11; r++)
                for (int c = 5; c < 11; c++) sumCR += normRaw[r, c];

            double midLeft = sumML / 35.0;
            double midRight = sumMR / 35.0;
            double upperMidLeftOpen = sumUML / 15.0;
            double centerRaw = sumCR / 30.0;

            int sumTA = 0, sumBA = 0, sumIH = 0;
            for (int r = 1; r < 4; r++)
                for (int c = 4; c < 12; c++) sumTA += normOpen[r, c];
            for (int r = 11; r < 15; r++)
                for (int c = 4; c < 12; c++) sumBA += normOpen[r, c];
            for (int r = 5; r < 10; r++)
                for (int c = 6; c < 10; c++) sumIH += normOpen[r, c];

            double topArch = sumTA / 24.0;
            double botArch = sumBA / 32.0;
            double innerHole = sumIH / 20.0;

            string bestSym = (allowedSymbols.Count > 0) ? allowedSymbols[0] : "?";
            double bestScore = -1.0;
            outAltSym = bestSym;
            outAltScore = -1.0;

            for (int i = 0; i < allowedSymbols.Count; i++)
            {
                string symKey = allowedSymbols[i];
                List<string> variants = new List<string>();
                variants.Add(symKey);
                if (char.IsLetter(symKey[0])) variants.Add(symKey.ToLowerInvariant());

                double symScore = -1.0;
                for (int v = 0; v < variants.Count; v++)
                {
                    List<int[,]> tmpls;
                    if (!_rotatedSymBank.TryGetValue(variants[v], out tmpls)) continue;
                    for (int t = 0; t < tmpls.Count; t++)
                    {
                        double sRaw = ScoreBinary2D(normRaw, tmpls[t]);
                        double sOpen = ScoreBinary2D(normOpen, tmpls[t]);
                        double s;
                        if (symKey == "@" || symKey == "%" || symKey == "$")
                            s = Math.Max(sRaw, 0.55 * sOpen + 0.45 * sRaw);
                        else
                            s = (midLeft > 0.15) ? (0.65 * sOpen + 0.35 * sRaw) : sRaw;
                        if (s > symScore) symScore = s;
                    }
                }

                if ((symKey == "N" || symKey == "M" || symKey == "H" || symKey == "U") && (midLeft < 0.35 || midRight < 0.30))
                    symScore -= 0.18;
                int sumMRRaw = 0, sumTARaw = 0, sumBARaw = 0;
                for (int r = 4; r < 11; r++) for (int c = 9; c < 15; c++) sumMRRaw += normRaw[r, c];
                for (int r = 1; r < 4; r++) for (int c = 5; c < 10; c++) sumTARaw += normRaw[r, c];
                for (int r = 12; r < 15; r++) for (int c = 5; c < 10; c++) sumBARaw += normRaw[r, c];
                double midRightRaw = sumMRRaw / 42.0;
                double topArchRaw = sumTARaw / 15.0;
                double botArchRaw = sumBARaw / 15.0;

                if (topArch > 0.50 && botArch > 0.50 && innerHole < 0.25)
                {
                    if ("NMWZXVKY".IndexOf(symKey, StringComparison.Ordinal) >= 0) symScore -= 0.22;
                    if (midRight > 0.25 && "DOBQ0".IndexOf(symKey, StringComparison.Ordinal) >= 0) symScore += 0.10;
                    else if (midRight < 0.18 && symKey == "C") symScore += 0.12;
                }
                if (symKey == "C")
                {
                    if (midRightRaw > 0.25 || midRight > 0.25) symScore -= 0.25;
                    else if (midRightRaw < 0.12) symScore += 0.15;
                }
                if (symKey == "%" && topArchRaw > 0.50 && botArchRaw > 0.50)
                    symScore -= 0.20;
                if (symKey == "B")
                {
                    if (midRightRaw < 0.18 || (topArchRaw < 0.25 && botArchRaw < 0.25)) symScore -= 0.25;
                    else if (midRightRaw > 0.35 && centerRaw > 0.35 && topArchRaw > 0.40 && botArchRaw > 0.40) symScore += 0.12;
                }
                if (symKey == "Z" && midLeft > 0.32) symScore -= 0.12;
                if (symKey == "@" && upperMidLeftOpen < 0.25 && centerRaw > 0.35 && subRaw.GetLength(1) >= 28)
                    symScore += 0.22;
                if (symKey == "U" && centerRaw > 0.30)
                    symScore -= 0.25;
                int topLLoc = 0, topCLoc = 0, topRLoc = 0, midRLoc = 0;
                for (int r = 1; r < 5; r++)
                {
                    for (int c = 0; c < 4; c++) topLLoc += normLoc[r, c];
                    for (int c = 5; c < 11; c++) topCLoc += normLoc[r, c];
                    for (int c = 12; c < 16; c++) topRLoc += normLoc[r, c];
                }
                for (int r = 6; r < 10; r++)
                    for (int c = 10; c < 15; c++) midRLoc += normLoc[r, c];
                if (topLLoc == 0 && topRLoc == 0 && (topCLoc / 24.0) >= 0.35)
                {
                    if (symKey == "T") symScore += 0.12;
                    else if (symKey == "W" || symKey == "M" || symKey == "U" || symKey == "L") symScore -= 0.15;
                }
                if (symKey == "L" && subRaw.GetLength(1) >= 22 && midRLoc >= 4)
                    symScore -= 0.20;
                if (symKey == "E" && midRight > 0.30)
                    symScore -= 0.22;
                if (innerHole > 0.55)
                {
                    if (midLeft < 0.30 && midRight < 0.30)
                    {
                        if (symKey == "X") symScore += 0.18;
                        else if (symKey == "Q" || symKey == "O" || symKey == "D" || symKey == "C" || symKey == "G" || symKey == "U")
                            symScore -= 0.20;
                    }
                    else if (symKey == "&" && (midLeft >= 0.35 || midRight >= 0.35))
                    {
                        symScore += 0.22;
                    }
                }

                if (symScore > bestScore)
                {
                    outAltScore = bestScore;
                    outAltSym = bestSym;
                    bestScore = symScore;
                    bestSym = symKey;
                }
                else if (symScore > outAltScore && symKey != bestSym)
                {
                    outAltScore = symScore;
                    outAltSym = symKey;
                }
            }

            int runsT1 = 0, inR = 0;
            for (int c = 0; c < 16; c++) { if (normOpen[1, c] != 0 && inR == 0) { runsT1++; inR = 1; } else if (normOpen[1, c] == 0) inR = 0; }
            int runsT2 = 0; inR = 0;
            for (int c = 0; c < 16; c++) { if (normOpen[2, c] != 0 && inR == 0) { runsT2++; inR = 1; } else if (normOpen[2, c] == 0) inR = 0; }
            int runsB13 = 0; inR = 0;
            for (int c = 0; c < 16; c++) { if (normOpen[13, c] != 0 && inR == 0) { runsB13++; inR = 1; } else if (normOpen[13, c] == 0) inR = 0; }
            int runsB14 = 0; inR = 0;
            for (int c = 0; c < 16; c++) { if (normOpen[14, c] != 0 && inR == 0) { runsB14++; inR = 1; } else if (normOpen[14, c] == 0) inR = 0; }

            int centerF = 0;
            for (int r = 5; r < 9; r++) for (int c = 7; c < 9; c++) centerF += normOpen[r, c];
            bool wings = (normOpen[6, 0] != 0 || normOpen[6, 1] != 0 || normOpen[6, 2] != 0 || normOpen[7, 0] != 0 || normOpen[7, 1] != 0 || normOpen[7, 2] != 0) &&
                         (normOpen[6, 13] != 0 || normOpen[6, 14] != 0 || normOpen[6, 15] != 0 || normOpen[7, 13] != 0 || normOpen[7, 14] != 0 || normOpen[7, 15] != 0);
            bool isHash = (Math.Max(runsT1, runsT2) >= 2 && Math.Max(runsB13, runsB14) >= 2 && centerF >= 2 && wings);

            int botRCorner = 0;
            for (int r = 13; r < 16; r++) for (int c = 11; c < 15; c++) botRCorner += normOpen[r, c];
            int loopFill = 0;
            for (int r = 4; r < 9; r++) for (int c = 9; c < 14; c++) loopFill += normOpen[r, c];

            if (allowedSymbols.Contains("#") && isHash)
            {
                bestSym = "#";
                bestScore = 0.88;
            }
            else if (allowedSymbols.Contains("P") && botRCorner == 0 && loopFill > 8 && bestSym == "S")
            {
                bestSym = "P";
                bestScore = 0.78;
            }

            outScore = Math.Round(bestScore, 3);
            return bestSym;
        }

        private static List<TopDetectedItem> ExtractTopItems(byte[,,] rgb, int H, int W, List<LegendEntry> legendEntries)
        {
            int yTop = Math.Min(66, (int)(H * 0.27));
            int[,] fgLoc = RemoveHorizontalLinesPure(rgb, yTop, W, 51);
            Dictionary<string, int[,]> rawMasks = BuildColorMasksPure(rgb, 0, yTop, W);

            List<string> allowedSymbols = new List<string>();
            for (int i = 0; i < legendEntries.Count; i++)
            {
                string s = legendEntries[i].Symbol;
                if (!string.IsNullOrEmpty(s) && s != "?" && !allowedSymbols.Contains(s))
                    allowedSymbols.Add(s);
            }

            List<TopDetectedItem> items = new List<TopDetectedItem>();
            for (int ci = 0; ci < ORDER.Length; ci++)
            {
                string colorName = ORDER[ci];
                int[,] rawM = rawMasks[colorName];
                int[,] locM = new int[yTop, W];
                int xLimit = Math.Min(235, W);
                for (int y = 0; y < yTop; y++)
                    for (int x = 24; x < xLimit; x++)
                        if (rawM[y, x] != 0 && fgLoc[y, x] != 0) locM[y, x] = 1;

                int[,] locU8 = MorphClose(MorphOpen(locM, 1, 2), 5, 7);
                List<CompItem> comps = ConnectedComponents(locU8);
                List<ClusterItem> clusters = new List<ClusterItem>();
                for (int i = 0; i < comps.Count; i++)
                {
                    CompItem c = comps[i];
                    if (c.Area >= 25 && c.H >= 7 && c.W >= 4)
                        clusters.Add(new ClusterItem(c.XMean, c.Area, c.X, c.Y, c.W, c.H));
                }
                clusters.Sort(delegate(ClusterItem a, ClusterItem b) { return a.XMean.CompareTo(b.XMean); });

                List<ClusterItem> merged = new List<ClusterItem>();
                for (int i = 0; i < clusters.Count; i++)
                {
                    ClusterItem cl = clusters[i];
                    if (merged.Count == 0) merged.Add(cl);
                    else
                    {
                        ClusterItem prev = merged[merged.Count - 1];
                        if (Math.Abs(cl.XMean - prev.XMean) < 25.0 || cl.X <= prev.X + prev.W + 4)
                        {
                            double totA = prev.Area + cl.Area;
                            double nxM = (prev.XMean * prev.Area + cl.XMean * cl.Area) / totA;
                            int nx0 = Math.Min(prev.X, cl.X), ny0 = Math.Min(prev.Y, cl.Y);
                            int nx1 = Math.Max(prev.X + prev.W, cl.X + cl.W), ny1 = Math.Max(prev.Y + prev.H, cl.Y + cl.H);
                            merged[merged.Count - 1] = new ClusterItem(nxM, totA, nx0, ny0, nx1 - nx0, ny1 - ny0);
                        }
                        else merged.Add(cl);
                    }
                }

                List<ClusterItem> validMerged = new List<ClusterItem>();
                for (int i = 0; i < merged.Count; i++)
                {
                    if (merged[i].H >= 14 && merged[i].Area >= 40) validMerged.Add(merged[i]);
                }
                if (validMerged.Count == 0) continue;

                validMerged.Sort(delegate(ClusterItem a, ClusterItem b) { return b.Area.CompareTo(a.Area); });
                List<ClusterItem> kept = new List<ClusterItem>();
                kept.Add(validMerged[0]);
                for (int i = 1; i < validMerged.Count; i++)
                {
                    if (validMerged[i].Area >= 130 && validMerged[i].H >= 18) kept.Add(validMerged[i]);
                }
                kept.Sort(delegate(ClusterItem a, ClusterItem b) { return a.XMean.CompareTo(b.XMean); });

                for (int i = 0; i < kept.Count; i++)
                {
                    ClusterItem k = kept[i];


                    int minIx = W, maxIx = -1, minIy = yTop, maxIy = -1, cntIn = 0;
                    int ixStart = Math.Max(24, (int)(k.XMean - 17));
                    int ixEnd = Math.Min(W - 18, (int)(k.XMean + 18));
                    for (int iy = 0; iy < yTop; iy++)
                    {
                        for (int ix = ixStart; ix < ixEnd; ix++)
                        {
                            if (locU8[iy, ix] != 0)
                            {
                                cntIn++;
                                if (ix < minIx) minIx = ix;
                                if (ix > maxIx) maxIx = ix;
                                if (iy < minIy) minIy = iy;
                                if (iy > maxIy) maxIy = iy;
                            }
                        }
                    }
                    int x0, x1, y0, y1;
                    if (cntIn >= 10)
                    {
                        x0 = Math.Max(24, minIx); x1 = Math.Min(W - 18, maxIx + 1);
                        y0 = Math.Max(0, minIy); y1 = Math.Min(yTop, maxIy + 1);
                    }
                    else
                    {
                        x0 = Math.Max(24, k.X); x1 = Math.Min(W - 18, k.X + k.W);
                        y0 = Math.Max(0, k.Y); y1 = Math.Min(yTop, k.Y + k.H);
                    }
                    int[,] subRawSingle = Crop2D(rawM, y0, y1, x0, x1);
                    int[,] subLocSingle = Crop2D(locM, y0, y1, x0, x1);
                    double symSc, altSc;
                    string altSym;
                    string symPred = ClassifyTopGlyph(subRawSingle, subLocSingle, allowedSymbols, out symSc, out altSym, out altSc);
                    TopDetectedItem item = new TopDetectedItem();
                    item.X = Math.Round(k.XMean, 1); item.Color = colorName; item.Symbol = symPred;
                    item.SymScore = symSc; item.AltSymbol = altSym; item.AltScore = altSc;
                    item.Area = k.Area; item.W = x1 - x0; item.H = y1 - y0;
                    items.Add(item);
                }
            }

            items.Sort(delegate(TopDetectedItem a, TopDetectedItem b) { return a.X.CompareTo(b.X); });
            if (items.Count > 6)
            {
                items.Sort(delegate(TopDetectedItem a, TopDetectedItem b) { return b.Area.CompareTo(a.Area); });
                items = items.GetRange(0, 6);
                items.Sort(delegate(TopDetectedItem a, TopDetectedItem b) { return a.X.CompareTo(b.X); });
            }
            return items;
        }

        public static string SolveImage(string imagePath, out string debugInfo)
        {
            string fb;
            return SolveImageBytes(File.ReadAllBytes(imagePath), out fb, out debugInfo);
        }

        public static string SolveImageBytes(byte[] pngBytes, out string fallbackAnswer, out string debugInfo)
        {
            fallbackAnswer = null;
            InitBanks();
            int H, W;
            byte[,,] rgb = DecodePngBytesPure(pngBytes, out H, out W);
            List<LegendEntry> legend = ExtractLegendEntries(rgb, H, W);
            if (legend.Count == 0)
            {
                debugInfo = "No legend entries";
                return null;
            }

            Dictionary<string, string> symToDigit = new Dictionary<string, string>();
            Dictionary<string, string> colToDigit = new Dictionary<string, string>();
            StringBuilder mapSb = new StringBuilder();
            for (int i = 0; i < legend.Count; i++)
            {
                LegendEntry le = legend[i];
                colToDigit[le.ColorName] = le.Digit;
                if (!string.IsNullOrEmpty(le.Symbol) && le.Symbol != "?")
                    symToDigit[le.Symbol.ToUpperInvariant()] = le.Digit;
                if (i > 0) mapSb.Append(", ");
                mapSb.Append(le.Symbol).Append("->").Append(le.Digit);
            }

            List<TopDetectedItem> topItems = ExtractTopItems(rgb, H, W, legend);
            StringBuilder ansSb = new StringBuilder();
            StringBuilder charsSb = new StringBuilder();
            string[] primaryDigits = new string[topItems.Count];

            int weakestIdx = -1;
            double smallestGap = 999.0;

            for (int i = 0; i < topItems.Count; i++)
            {
                TopDetectedItem it = topItems[i];
                charsSb.Append(it.Symbol);
                string cDig = colToDigit.ContainsKey(it.Color) ? colToDigit[it.Color] : "1";
                string sDig = symToDigit.ContainsKey(it.Symbol) ? symToDigit[it.Symbol] : cDig;
                primaryDigits[i] = sDig;
                ansSb.Append(sDig);

                double gap = it.SymScore - it.AltScore;
                if (!string.IsNullOrEmpty(it.AltSymbol) && it.AltSymbol != it.Symbol && symToDigit.ContainsKey(it.AltSymbol) && gap < smallestGap)
                {
                    smallestGap = gap;
                    weakestIdx = i;
                }
            }

            if (weakestIdx >= 0 && topItems.Count > 0)
            {
                StringBuilder fbSb = new StringBuilder();
                for (int i = 0; i < topItems.Count; i++)
                {
                    if (i == weakestIdx)
                        fbSb.Append(symToDigit[topItems[i].AltSymbol]);
                    else
                        fbSb.Append(primaryDigits[i]);
                }
                fallbackAnswer = fbSb.ToString();
            }

            debugInfo = string.Format("top_chars={0} | sym_map={{{1}}} | fallback={2}",
                charsSb.ToString(), mapSb.ToString(), fallbackAnswer ?? "none");
            return ansSb.ToString();
        }

                private static int _roundRobinWinIdx = 0;

        private static List<IntPtr> FindAllGameWindowHandles(int targetPid)
        {
            List<KeyValuePair<string, IntPtr>> namedList = new List<KeyValuePair<string, IntPtr>>();
            IntPtr exactPidHwnd = IntPtr.Zero;

            EnumWindows(delegate(IntPtr hWnd, IntPtr lParam)
            {
                if (!IsWindowVisible(hWnd)) return true;
                RECT r;
                if (!GetClientRect(hWnd, out r) || (r.Right - r.Left) < 300 || (r.Bottom - r.Top) < 200)
                    return true;

                uint winPid;
                GetWindowThreadProcessId(hWnd, out winPid);
                if (targetPid > 0 && (int)winPid == targetPid)
                {
                    exactPidHwnd = hWnd;
                }

                StringBuilder sb = new StringBuilder(256);
                GetWindowText(hWnd, sb, 256);
                string title = sb.ToString();
                string lower = title.ToLowerInvariant();
                if (lower.Contains("mod 250") || lower.Contains("nro") || lower.Contains("dragonboy"))
                {
                    if (!lower.Contains("powershell") && !lower.Contains("cmd") && !lower.Contains("explorer") && !lower.Contains("visual studio"))
                    {
                        namedList.Add(new KeyValuePair<string, IntPtr>(title, hWnd));
                    }
                }
                return true;
            }, IntPtr.Zero);

            namedList.Sort(delegate(KeyValuePair<string, IntPtr> a, KeyValuePair<string, IntPtr> b)
            {
                return string.Compare(a.Key, b.Key, StringComparison.OrdinalIgnoreCase);
            });

            List<IntPtr> result = new List<IntPtr>();
            if (exactPidHwnd != IntPtr.Zero)
            {
                result.Add(exactPidHwnd);
            }
            for (int i = 0; i < namedList.Count; i++)
            {
                if (!result.Contains(namedList[i].Value))
                    result.Add(namedList[i].Value);
            }
            return result;
        }

        private static void ForceBringWindowToFront(IntPtr hwnd)
        {
            try
            {
                if (IsIconic(hwnd))
                {
                    ShowWindow(hwnd, 9);
                    Thread.Sleep(120);
                }
                IntPtr fgHwnd = GetForegroundWindow();
                uint fgPid;
                uint fgThread = (fgHwnd != IntPtr.Zero) ? GetWindowThreadProcessId(fgHwnd, out fgPid) : 0;
                uint curThread = GetCurrentThreadId();
                bool attached = false;
                if (fgThread != 0 && fgThread != curThread)
                {
                    attached = AttachThreadInput(fgThread, curThread, true);
                }
                // Đẩy cửa sổ game vượt lên trên PowerShell và mọi cửa sổ khác (TOPMOST -> NOTOPMOST)
                SetWindowPos(hwnd, new IntPtr(-1), 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040);
                SetWindowPos(hwnd, new IntPtr(-2), 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040);
                keybd_event(0x12, 0, 0, UIntPtr.Zero);
                BringWindowToTop(hwnd);
                SetForegroundWindow(hwnd);
                keybd_event(0x12, 0, 2, UIntPtr.Zero);
                if (attached)
                {
                    AttachThreadInput(fgThread, curThread, false);
                }
                Thread.Sleep(120);
            }
            catch (Exception) { }
        }

        // Kiểm tra trực tiếp trên màn hình xem cửa sổ hwnd có đang hiển thị bảng CAPTCHA (dải trắng ở giữa hoặc 5 nút cam ở dưới) không!
        // Giúp tránh 100% lỗi bấm nhầm vào tab game đang chơi bình thường khi treo nhiều nick!
        private static bool WindowHasCaptchaOpen(IntPtr hwnd, int cw, int ch)
        {
            IntPtr hdc = IntPtr.Zero;
            try
            {
                hdc = GetDC(IntPtr.Zero);
                if (hdc == IntPtr.Zero) return true;

                // 1. Kiểm tra 5 nút cam ở đáy cửa sổ (rel_y = 0.9015)
                int orangeCount = 0;
                for (int i = 0; i < 5; i++)
                {
                    POINT pt = new POINT();
                    pt.X = (int)(cw * ORANGE_BTN_X_PCTS[i]);
                    pt.Y = (int)(ch * ORANGE_BTN_Y_PCT);
                    ClientToScreen(hwnd, ref pt);
                    uint c = GetPixel(hdc, pt.X, pt.Y);
                    if (c != 0xFFFFFFFF)
                    {
                        int r = (int)(c & 0xFF);
                        int g = (int)((c >> 8) & 0xFF);
                        int b = (int)((c >> 16) & 0xFF);
                        if (r >= 180 && g >= 40 && g <= 165 && b <= 65 && (r - b) >= 120)
                            orangeCount++;
                    }
                }
                if (orangeCount >= 3) return true;

                // 2. Kiểm tra dải trắng giữa bảng CAPTCHA (rel_x = 0.45..0.60, rel_y = 0.35)
                int whiteCount = 0;
                double[] sampleXs = new double[] { 0.45, 0.49, 0.53, 0.57, 0.61 };
                for (int i = 0; i < sampleXs.Length; i++)
                {
                    POINT pt = new POINT();
                    pt.X = (int)(cw * sampleXs[i]);
                    pt.Y = (int)(ch * 0.35);
                    ClientToScreen(hwnd, ref pt);
                    uint c = GetPixel(hdc, pt.X, pt.Y);
                    if (c != 0xFFFFFFFF)
                    {
                        int r = (int)(c & 0xFF);
                        int g = (int)((c >> 8) & 0xFF);
                        int b = (int)((c >> 16) & 0xFF);
                        if (r >= 235 && g >= 235 && b >= 235 && Math.Abs(r - b) <= 15)
                            whiteCount++;
                    }
                }
                return whiteCount >= 3;
            }
            catch (Exception)
            {
                return true;
            }
            finally
            {
                if (hdc != IntPtr.Zero) ReleaseDC(IntPtr.Zero, hdc);
            }
        }

        private static string ClickDigitsOnWindow(IntPtr hwnd, int cw, int ch, string winTitle, string codeToClick, string inboxDir)
        {
            Dictionary<char, int[]> digitCoords = new Dictionary<char, int[]>();
            char[] btnOrder = new char[] { '1', '3', '5', '7', '9' };
            for (int i = 0; i < 5; i++)
            {
                POINT pt = new POINT();
                pt.X = (int)(cw * ORANGE_BTN_X_PCTS[i]);
                pt.Y = (int)(ch * ORANGE_BTN_Y_PCT);
                ClientToScreen(hwnd, ref pt);
                digitCoords[btnOrder[i]] = new int[] { pt.X, pt.Y };
            }

            for (int i = 0; i < codeToClick.Length; i++)
            {
                if (i > 0 && !string.IsNullOrEmpty(inboxDir))
                {
                    try
                    {
                        if (Directory.GetFiles(inboxDir, "*.png").Length > 0)
                        {
                            Thread.Sleep(200);
                            return string.Format("aborted_on_new_captcha_at_digit_{0}(win='{1}')", i, winTitle);
                        }
                    }
                    catch (Exception) { }
                }

                char dig = codeToClick[i];
                int[] xy;
                if (digitCoords.TryGetValue(dig, out xy))
                {
                    POINT userCur;
                    bool hasCur = GetCursorPos(out userCur);

                    int clientX = (int)(cw * ORANGE_BTN_X_PCTS["13579".IndexOf(dig)]);
                    int clientY = (int)(ch * ORANGE_BTN_Y_PCT);
                    IntPtr lParam = (IntPtr)((clientY << 16) | (clientX & 0xFFFF));
                    PostMessage(hwnd, 0x0200, IntPtr.Zero, lParam);
                    PostMessage(hwnd, 0x0201, (IntPtr)1, lParam);
                    PostMessage(hwnd, 0x0202, IntPtr.Zero, lParam);

                    SetCursorPos(xy[0], xy[1]);
                    Thread.Sleep(8);
                    mouse_event(0x0002, 0, 0, 0, UIntPtr.Zero);
                    Thread.Sleep(8);
                    mouse_event(0x0004, 0, 0, 0, UIntPtr.Zero);
                    if (hasCur)
                    {
                        SetCursorPos(userCur.X, userCur.Y);
                    }
                }
                Thread.Sleep(240);
            }
            return "ok";
        }

        public static string AutoClickOrangeButtons(string answer, string fallbackAnswer, int targetPid, string inboxDir)
        {
            List<IntPtr> windows = FindAllGameWindowHandles(targetPid);
            if (windows.Count == 0) return "no_window_found";

            try
            {
                IntPtr chosenHwnd = IntPtr.Zero;
                int cw = 0, ch = 0;
                string winTitle = "";

                if (targetPid > 0)
                {
                    chosenHwnd = windows[0];
                    ForceBringWindowToFront(chosenHwnd);
                    RECT r;
                    if (GetClientRect(chosenHwnd, out r)) { cw = r.Right - r.Left; ch = r.Bottom - r.Top; }
                    StringBuilder sb = new StringBuilder(128);
                    GetWindowText(chosenHwnd, sb, 128);
                    winTitle = sb.ToString();
                }
                else
                {
                    // Quét qua các cửa sổ game để tìm đúng cửa sổ THỰC SỰ ĐANG CÓ BẢNG CAPTCHA trên màn hình!
                    int startIdx = _roundRobinWinIdx % windows.Count;
                    _roundRobinWinIdx++;
                    for (int w = 0; w < windows.Count; w++)
                    {
                        IntPtr cand = windows[(startIdx + w) % windows.Count];
                        ForceBringWindowToFront(cand);
                        RECT r;
                        if (!GetClientRect(cand, out r)) continue;
                        int candW = r.Right - r.Left;
                        int candH = r.Bottom - r.Top;
                        if (candW < 200 || candH < 150) continue;

                        if (windows.Count == 1 || WindowHasCaptchaOpen(cand, candW, candH))
                        {
                            chosenHwnd = cand;
                            cw = candW;
                            ch = candH;
                            StringBuilder sb = new StringBuilder(128);
                            GetWindowText(cand, sb, 128);
                            winTitle = sb.ToString();
                            break;
                        }
                    }
                    if (chosenHwnd == IntPtr.Zero)
                    {
                        chosenHwnd = windows[startIdx];
                        ForceBringWindowToFront(chosenHwnd);
                        RECT r;
                        if (GetClientRect(chosenHwnd, out r)) { cw = r.Right - r.Left; ch = r.Bottom - r.Top; }
                        StringBuilder sb = new StringBuilder(128);
                        GetWindowText(chosenHwnd, sb, 128);
                        winTitle = sb.ToString();
                    }
                }

                if (cw < 200 || ch < 150) return "invalid_rect";

                string step1 = ClickDigitsOnWindow(chosenHwnd, cw, ch, winTitle, answer, inboxDir);
                if (step1 != "ok") return step1;

                // PHƯƠNG ÁN DỰ PHÒNG (FALLBACK):
                // Sau khi bấm xong mã chính, chờ 320ms. Nếu chưa có ảnh CAPTCHA mới trong inbox
                // mà trên màn hình cửa sổ vẫn còn bảng CAPTCHA (chưa đóng) và có mã dự phòng khác mã chính -> thử ngay mã dự phòng!
                if (!string.IsNullOrEmpty(fallbackAnswer) && fallbackAnswer != answer)
                {
                    Thread.Sleep(320);
                    bool hasNewPng = false;
                    if (!string.IsNullOrEmpty(inboxDir))
                    {
                        try { hasNewPng = (Directory.GetFiles(inboxDir, "*.png").Length > 0); } catch (Exception) { }
                    }
                    if (!hasNewPng && WindowHasCaptchaOpen(chosenHwnd, cw, ch))
                    {
                        string step2 = ClickDigitsOnWindow(chosenHwnd, cw, ch, winTitle, fallbackAnswer, inboxDir);
                        return string.Format("clicked_ok_with_fallback:{0}->{1}(win='{2}',hwnd={3},{4}x{5},total_wins={6})",
                            answer, fallbackAnswer, winTitle, chosenHwnd, cw, ch, windows.Count);
                    }
                }

                return string.Format("clicked_ok(win='{0}',hwnd={1},{2}x{3},total_wins={4})", winTitle, chosenHwnd, cw, ch, windows.Count);
            }
            catch (Exception ex)
            {
                return "click_err:" + ex.Message;
            }
        }

        private static int ReadTargetPidFromJob(string jobsDir, string sha)
        {
            try
            {
                string jobPath = Path.Combine(jobsDir, sha + ".json");
                // Chờ tối đa 90ms (6 x 15ms) vì NroPort.Plugin.dll ghi inbox/<sha>.png trước rồi mới ghi jobs/<sha>.json!
                for (int wait = 0; wait < 6; wait++)
                {
                    if (File.Exists(jobPath)) break;
                    Thread.Sleep(15);
                }
                if (!File.Exists(jobPath)) return 0;
                string txt = File.ReadAllText(jobPath, Encoding.UTF8);
                int idx = txt.IndexOf("\"pid\"", StringComparison.OrdinalIgnoreCase);
                if (idx < 0) return 0;
                int colon = txt.IndexOf(':', idx);
                if (colon < 0) return 0;
                StringBuilder numSb = new StringBuilder();
                for (int i = colon + 1; i < txt.Length; i++)
                {
                    char c = txt[i];
                    if (char.IsDigit(c)) numSb.Append(c);
                    else if (numSb.Length > 0) break;
                }
                int pid;
                if (int.TryParse(numSb.ToString(), out pid)) return pid;
            }
            catch (Exception) { }
            return 0;
        }

        private static void AppendLog(string logPath, string msg)
        {
            string line = string.Format("[{0}] {1}", DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"), msg);
            try
            {
                File.AppendAllText(logPath, line + Environment.NewLine, Encoding.UTF8);
            }
            catch (Exception) { }
            try
            {
                Console.WriteLine(line);
            }
            catch (Exception) { }
        }

        public static void RunWatchLoop(string queueDir)
        {
            bool createdNew = false;
            try
            {
                _singleInstanceMutex = new Mutex(true, @"Local\NroAutoCaptchaActiveWorkerMutex_v8_1", out createdNew);
                if (!createdNew)
                {
                    return;
                }
            }
            catch (Exception) { }

            InitBanks();
            string inboxDir = Path.Combine(queueDir, "inbox");
            string jobsDir = Path.Combine(queueDir, "jobs");
            string outboxDir = Path.Combine(queueDir, "outbox");
            string logPath = Path.Combine(queueDir, "solver.log");
            string lastSolvedBackup = Path.Combine(queueDir, "last_solved.png");
            Directory.CreateDirectory(inboxDir);
            Directory.CreateDirectory(jobsDir);
            Directory.CreateDirectory(outboxDir);

            // DỌN SẠCH TOÀN BỘ ẢNH CŨ TỒN ĐỌNG TRONG INBOX KHI KHỞI ĐỘNG (chỉ giữ 1 bản backup mới nhất)
            int deletedOldCount = 0;
            try
            {
                string[] existingPngs = Directory.GetFiles(inboxDir, "*.png");
                Array.Sort(existingPngs, delegate(string a, string b)
                {
                    return File.GetLastWriteTimeUtc(a).CompareTo(File.GetLastWriteTimeUtc(b));
                });
                if (existingPngs.Length > 0)
                {
                    try { File.Copy(existingPngs[existingPngs.Length - 1], lastSolvedBackup, true); } catch (Exception) { }
                }
                DateTime nowUtc = DateTime.UtcNow;
                for (int i = 0; i < existingPngs.Length; i++)
                {
                    if ((nowUtc - File.GetLastWriteTimeUtc(existingPngs[i])).TotalSeconds > 5.0)
                    {
                        try { File.Delete(existingPngs[i]); deletedOldCount++; } catch (Exception) { }
                    }
                }
            }
            catch (Exception) { }

            AppendLog(logPath, string.Format("SAN SANG V8.1 (Chuan 8/8 Captcha + Tach Muit Ten i/t/l + 5 Ky Hieu Doc Lap + Nhan Dien Tab) (Ho tro nhieu nick + Tu dong xoa {0} anh cu)! Dang theo doi tai: {1}", deletedOldCount, queueDir));

            HashSet<string> processed = new HashSet<string>();

            while (true)
            {
                try
                {
                    string[] pngFiles = Directory.GetFiles(inboxDir, "*.png");
                    if (pngFiles.Length > 0)
                    {
                        // Sắp xếp theo thời gian từ cũ đến mới
                        Array.Sort(pngFiles, delegate(string a, string b)
                        {
                            return File.GetLastWriteTimeUtc(a).CompareTo(File.GetLastWriteTimeUtc(b));
                        });

                        List<IntPtr> openWins = FindAllGameWindowHandles(0);
                        int maxActive = Math.Max(1, openWins.Count);

                        // NẾU CÓ NHIỀU ẢNH HƠN SỐ CỬA SỔ GAME -> XOÁ NGAY CÁC ẢNH CŨ ĐÃ HẾT HẠN ĐỂ CHỈ GIẢI ẢNH MỚI NHẤT!
                        if (pngFiles.Length > maxActive)
                        {
                            int toDelete = pngFiles.Length - maxActive;
                            for (int d = 0; d < toDelete; d++)
                            {
                                try
                                {
                                    string oldSha = Path.GetFileNameWithoutExtension(pngFiles[d]);
                                    File.Delete(pngFiles[d]);
                                    string oldJob = Path.Combine(jobsDir, oldSha + ".json");
                                    if (File.Exists(oldJob)) File.Delete(oldJob);
                                }
                                catch (Exception) { }
                            }
                            // Chỉ giữ lại các ảnh mới nhất tương ứng với số nick đang mở
                            string[] newestFiles = new string[maxActive];
                            Array.Copy(pngFiles, pngFiles.Length - maxActive, newestFiles, 0, maxActive);
                            pngFiles = newestFiles;
                        }

                        for (int i = 0; i < pngFiles.Length; i++)
                        {
                            string pngPath = pngFiles[i];
                            if (!File.Exists(pngPath)) continue;
                            string sha = Path.GetFileNameWithoutExtension(pngPath);
                            if (processed.Contains(sha))
                            {
                                try { File.Delete(pngPath); } catch (Exception) { }
                                continue;
                            }

                            byte[] pngBytes = null;
                            for (int retry = 0; retry < 5; retry++)
                            {
                                try
                                {
                                    FileInfo fi = new FileInfo(pngPath);
                                    if (fi.Exists && fi.Length > 200)
                                    {
                                        pngBytes = File.ReadAllBytes(pngPath);
                                        break;
                                    }
                                }
                                catch (Exception) { }
                                Thread.Sleep(15);
                            }
                            if (pngBytes == null || pngBytes.Length < 200) continue;

                            // XOÁ NGAY LẬP TỨC FILE PNG TRONG INBOX (< 1ms) TRƯỚC KHI GIẢI
                            // để không bất kỳ tiến trình ngầm hay DLL cũ nào đọc trùng và bấm đúp!
                            try { File.Delete(pngPath); } catch (Exception) { }
                            try { File.WriteAllBytes(lastSolvedBackup, pngBytes); } catch (Exception) { }

                            int targetPid = ReadTargetPidFromJob(jobsDir, sha);
                            try
                            {
                                string jobFile = Path.Combine(jobsDir, sha + ".json");
                                if (File.Exists(jobFile)) File.Delete(jobFile);
                            }
                            catch (Exception) { }

                            Stopwatch sw = Stopwatch.StartNew();
                            string fallbackAnswer;
                            string debugInfo;
                            string answer = SolveImageBytes(pngBytes, out fallbackAnswer, out debugInfo);
                            sw.Stop();

                            if (!string.IsNullOrEmpty(answer))
                            {
                                string outPath = Path.Combine(outboxDir, sha + ".txt");
                                string tmpPath = Path.Combine(outboxDir, sha + ".tmp");
                                File.WriteAllText(tmpPath, answer, Encoding.UTF8);
                                if (File.Exists(outPath)) File.Delete(outPath);
                                File.Move(tmpPath, outPath);
                                processed.Add(sha);

                                string clickStatus = AutoClickOrangeButtons(answer, fallbackAnswer, targetPid, inboxDir);
                                AppendLog(logPath, string.Format("SOLVED ({0} so) {1} -> {2} ({3}ms) | input={4} | {5}",
                                    answer.Length, sha, answer, sw.ElapsedMilliseconds, clickStatus, debugInfo));
                            }
                            else
                            {
                                processed.Add(sha);
                                AppendLog(logPath, string.Format("FAIL {0} | {1}", sha, debugInfo));
                            }
                        }
                    }
                }
                catch (Exception ex)
                {
                    AppendLog(logPath, "ERROR: " + ex.Message);
                }
                Thread.Sleep(12);
            }
        }

        public static void Main(string[] args)
        {
            if (args != null && args.Length >= 1 && args[0].EndsWith(".png", StringComparison.OrdinalIgnoreCase))
            {
                Stopwatch sw = Stopwatch.StartNew();
                string dbg;
                string ans = SolveImage(args[0], out dbg);
                sw.Stop();
                Console.WriteLine(string.Format("{{\"file\": \"{0}\", \"time_ms\": {1}, \"answer\": \"{2}\", \"details\": \"{3}\"}}",
                    args[0].Replace("\\", "\\\\"), sw.ElapsedMilliseconds, ans, dbg));
                return;
            }

            string modRoot = ResolveModRootDir();
            string queueDir = EnsureRelativeConfigAndQueueDir(modRoot);
            RunWatchLoop(queueDir);
        }
    }
}