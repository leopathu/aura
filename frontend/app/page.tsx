import Link from 'next/link'

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="max-w-5xl w-full items-center justify-between font-mono text-sm">
        <div className="text-center">
          <h1 className="text-6xl font-bold mb-4 bg-gradient-to-r from-primary-600 to-accent-600 bg-clip-text text-transparent">
            Aura
          </h1>
          <p className="text-2xl mb-8 text-gray-600">
            Your Personal AI Assistant Platform
          </p>
          <p className="text-lg mb-12 text-gray-500 max-w-2xl mx-auto">
            Connect your favorite apps, bring your own AI models, and automate workflows 
            with intelligent agents powered by LangGraph.
          </p>

          <div className="flex gap-4 justify-center mb-16">
            <Link
              href="/register"
              className="px-8 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-semibold"
            >
              Get Started
            </Link>
            <Link
              href="/login"
              className="px-8 py-3 bg-white text-primary-600 border-2 border-primary-600 rounded-lg hover:bg-primary-50 transition-colors font-semibold"
            >
              Sign In
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-left">
            <div className="p-6 bg-white rounded-xl shadow-sm border border-gray-200">
              <div className="text-3xl mb-3">🔗</div>
              <h3 className="text-lg font-semibold mb-2">Connect Apps</h3>
              <p className="text-gray-600 text-sm">
                Link Gmail, Jira, Slack, Calendar, and more with one-click OAuth integration.
              </p>
            </div>

            <div className="p-6 bg-white rounded-xl shadow-sm border border-gray-200">
              <div className="text-3xl mb-3">🤖</div>
              <h3 className="text-lg font-semibold mb-2">AI Models</h3>
              <p className="text-gray-600 text-sm">
                Bring your own API keys for OpenAI, Claude, Gemini, and more. You control the cost.
              </p>
            </div>

            <div className="p-6 bg-white rounded-xl shadow-sm border border-gray-200">
              <div className="text-3xl mb-3">⚡</div>
              <h3 className="text-lg font-semibold mb-2">Automate</h3>
              <p className="text-gray-600 text-sm">
                Create workflows that run on schedules or triggers. Let AI handle the routine.
              </p>
            </div>
          </div>

          <div className="mt-16 text-gray-400 text-sm">
            <p>Open Source • Privacy First • Self-Hostable</p>
          </div>
        </div>
      </div>
    </main>
  )
}
