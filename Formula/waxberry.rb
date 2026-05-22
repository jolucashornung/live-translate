class Waxberry < Formula
  desc "Fully local, real-time English <-> Mandarin speech translator"
  homepage "https://github.com/jolucashornung/waxberry"
  url "https://github.com/jolucashornung/waxberry/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "PLACEHOLDER" # Run `brew fetch --build-from-source waxberry` after tagging to get this
  license "MIT"

  depends_on "node"
  depends_on "python@3.11"
  depends_on "espeak-ng"
  depends_on "sox"

  def install
    # ── Python virtual environment ─────────────────────────────────────────────
    venv = virtualenv_create(libexec/"venv", "python3.11")
    venv.pip_install_and_link buildpath/"requirements.txt"

    # Install Python service source code
    (share/"waxberry"/"services").mkpath
    %w[asr translation tts orchestrator].each do |svc|
      (share/"waxberry"/"services"/svc).install Dir["services/#{svc}/*"]
    end
    (share/"waxberry"/"shared").install Dir["shared/*"]

    # Download Piper voice models into the Homebrew share directory
    (share/"waxberry"/"voices").mkpath
    system libexec/"venv/bin/python3", "services/tts/scripts/download_voices.py",
           env: { "PIPER_VOICE_DIR" => (share/"waxberry"/"voices").to_s }

    # ── TypeScript CLI ─────────────────────────────────────────────────────────
    cd "cli" do
      system "npm", "ci", "--ignore-scripts"
      system "npm", "run", "build"
      (libexec/"cli").install "dist", "node_modules"
    end

    # Wrapper script: sets service paths and delegates to node
    (bin/"waxberry").write <<~SH
      #!/bin/bash
      export WAXBERRY_SERVICES_DIR="#{share}/waxberry/services"
      export WAXBERRY_UVICORN="#{libexec}/venv/bin/uvicorn"
      export PIPER_VOICE_DIR="#{share}/waxberry/voices"
      exec "#{Formula["node"].opt_bin}/node" "#{libexec}/cli/dist/index.js" "$@"
    SH
    chmod 0755, bin/"waxberry"
  end

  test do
    assert_match "0.1.0", shell_output("#{bin}/waxberry --version")
  end
end
