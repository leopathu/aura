export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-blue-50">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center max-w-4xl mx-auto">
          <h1 className="text-6xl font-bold mb-6 bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
            Aura
          </h1>
          <p className="text-2xl text-gray-700 mb-4">
            Your AI Agent Platform
          </p>
          <p className="text-lg text-gray-600 mb-12">
            Connect your favorite apps and LLM models. Let Aura handle tasks, analyze reports, and manage your work from a single place.
          </p>
          
          <div className="flex gap-4 justify-center mb-16">
            <a
              href="/auth/register"
              className="px-8 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium"
            >
              Get Started
            </a>
            <a
              href="/auth/login"
              className="px-8 py-3 bg-white text-purple-600 border-2 border-purple-600 rounded-lg hover:bg-purple-50 transition-colors font-medium"
            >
              Sign In
            </a>
          </div>

          <div className="grid md:grid-cols-3 gap-8 mt-16">
            <div className="p-6 bg-white rounded-xl shadow-sm">
              <div className="text-4xl mb-4">🔗</div>
              <h3 className="text-xl font-semibold mb-2">Connect Anything</h3>
              <p className="text-gray-600">
                Integrate Gmail, Slack, Notion, and more through MCP protocol
              </p>
            </div>
            
            <div className="p-6 bg-white rounded-xl shadow-sm">
              <div className="text-4xl mb-4">🤖</div>
              <h3 className="text-xl font-semibold mb-2">Bring Your Own Model</h3>
              <p className="text-gray-600">
                Use OpenAI, Anthropic, or Gemini with your own API keys
              </p>
            </div>
            
            <div className="p-6 bg-white rounded-xl shadow-sm">
              <div className="text-4xl mb-4">⚡</div>
              <h3 className="text-xl font-semibold mb-2">Outcome-Centric</h3>
              <p className="text-gray-600">
                Just ask what you need done. No complex workflows required.
              </p>
            </div>
          </div>

          <div className="mt-16 p-8 bg-white rounded-xl shadow-sm">
            <h2 className="text-3xl font-bold mb-6">How It Works</h2>
            <div className="space-y-4 text-left max-w-2xl mx-auto">
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-8 h-8 bg-purple-600 text-white rounded-full flex items-center justify-center font-bold">
                  1
                </div>
                <div>
                  <h4 className="font-semibold mb-1">Connect Your Apps</h4>
                  <p className="text-gray-600">Link Gmail, Slack, calendar, and other tools you use daily</p>
                </div>
              </div>
              
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-8 h-8 bg-purple-600 text-white rounded-full flex items-center justify-center font-bold">
                  2
                </div>
                <div>
                  <h4 className="font-semibold mb-1">Add Your API Key</h4>
                  <p className="text-gray-600">Bring your own OpenAI, Anthropic, or Gemini API key</p>
                </div>
              </div>
              
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-8 h-8 bg-purple-600 text-white rounded-full flex items-center justify-center font-bold">
                  3
                </div>
                <div>
                  <h4 className="font-semibold mb-1">Ask Aura</h4>
                  <p className="text-gray-600">Tell Aura what you need. Watch it analyze, plan, and execute</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
