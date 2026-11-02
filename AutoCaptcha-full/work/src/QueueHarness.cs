using NroAutoCaptchaMod;
public static class QueueHarness {
    public static void Main(string[] args) { CaptchaEmbeddedEngine.RunWatchLoop(args[0]); }
}
