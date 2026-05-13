import { ChatWidget } from '../components/ChatWidget';
import { LanguageProvider } from '../context/LanguageContext';
import { AccessibilityProvider } from '../context/AccessibilityContext';
import { BackendSettingsProvider } from '../context/BackendSettingsContext';

/**
 * Demo page showing how to use the ChatWidget component
 *
 * This demonstrates the plug-and-play nature of the widget.
 * Simply wrap it in the required providers and drop it into any page.
 */
export default function WidgetDemo() {
  return (
    <LanguageProvider>
      <AccessibilityProvider>
        <BackendSettingsProvider>
          <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 p-8">
            <div className="max-w-6xl mx-auto">
              {/* Demo Page Content */}
              <header className="mb-12">
                <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
                  Vecinita Chat Widget Demo
                </h1>
                <p className="text-lg text-gray-700 dark:text-gray-300">
                  This page demonstrates the plug-and-play ChatWidget component. The chat widget
                  appears in the bottom-right corner and can be embedded on any page.
                </p>
              </header>

              {/* Feature Cards */}
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                  <div className="w-12 h-12 bg-turquoise-500 rounded-lg flex items-center justify-center mb-4">
                    <svg
                      className="w-6 h-6 text-white"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z"
                      />
                    </svg>
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                    Easy Integration
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400">
                    Just import and drop the ChatWidget component into any page. No complex setup
                    required.
                  </p>
                </div>

                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                  <div className="w-12 h-12 bg-purple-500 rounded-lg flex items-center justify-center mb-4">
                    <svg
                      className="w-6 h-6 text-white"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"
                      />
                    </svg>
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                    Fully Customizable
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400">
                    Customize colors, position, theme, and messages to match your brand and needs.
                  </p>
                </div>

                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                  <div className="w-12 h-12 bg-green-500 rounded-lg flex items-center justify-center mb-4">
                    <svg
                      className="w-6 h-6 text-white"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129"
                      />
                    </svg>
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                    Bilingual Support
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400">
                    Built-in Spanish and English support with easy language switching.
                  </p>
                </div>

                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                  <div className="w-12 h-12 bg-orange-500 rounded-lg flex items-center justify-center mb-4">
                    <svg
                      className="w-6 h-6 text-white"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                      />
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                      />
                    </svg>
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                    Accessibility First
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400">
                    Includes screen reader support, dyslexic fonts, high contrast, and more.
                  </p>
                </div>

                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                  <div className="w-12 h-12 bg-pink-500 rounded-lg flex items-center justify-center mb-4">
                    <svg
                      className="w-6 h-6 text-white"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                      />
                    </svg>
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                    Smart & Responsive
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400">
                    Adapts to screen sizes and includes AI-powered responses with source citations.
                  </p>
                </div>

                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                  <div className="w-12 h-12 bg-indigo-500 rounded-lg flex items-center justify-center mb-4">
                    <svg
                      className="w-6 h-6 text-white"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                      />
                    </svg>
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                    Privacy Focused
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400">
                    Local storage for preferences, no unnecessary data collection or tracking.
                  </p>
                </div>
              </div>

              {/* Code Example */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mb-12">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                  How to Use
                </h2>
                <p className="text-gray-700 dark:text-gray-300 mb-4">
                  Simply import the ChatWidget and wrap your app with the required providers:
                </p>
                <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto">
                  <code>{`import { ChatWidget } from './components/ChatWidget';
import { LanguageProvider } from './context/LanguageContext';
import { AccessibilityProvider } from './context/AccessibilityContext';
import { BackendSettingsProvider } from './context/BackendSettingsContext';

function MyPage() {
  return (
    <LanguageProvider>
      <AccessibilityProvider>
        <BackendSettingsProvider>
          <div>
            {/* Your page content */}
            <h1>My Website</h1>
            
            {/* Drop in the chat widget */}
            <ChatWidget 
              position="bottom-right"
              primaryColor="#4DB8B8"
              defaultOpen={false}
            />
          </div>
        </BackendSettingsProvider>
      </AccessibilityProvider>
    </LanguageProvider>
  );
}`}</code>
                </pre>
              </div>

              {/* Props Documentation */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                  Available Props
                </h2>
                <div className="overflow-x-auto">
                  <table className="w-full text-left">
                    <thead>
                      <tr className="border-b border-gray-200 dark:border-gray-700">
                        <th className="py-3 px-4 text-gray-900 dark:text-white font-semibold">
                          Prop
                        </th>
                        <th className="py-3 px-4 text-gray-900 dark:text-white font-semibold">
                          Type
                        </th>
                        <th className="py-3 px-4 text-gray-900 dark:text-white font-semibold">
                          Default
                        </th>
                        <th className="py-3 px-4 text-gray-900 dark:text-white font-semibold">
                          Description
                        </th>
                      </tr>
                    </thead>
                    <tbody className="text-gray-700 dark:text-gray-300">
                      <tr className="border-b border-gray-100 dark:border-gray-700">
                        <td className="py-3 px-4 font-mono text-sm">position</td>
                        <td className="py-3 px-4 text-sm">
                          {"'bottom-right' | 'bottom-left' | 'top-right' | 'top-left'"}
                        </td>
                        <td className="py-3 px-4 text-sm">{"'bottom-right'"}</td>
                        <td className="py-3 px-4 text-sm">Position of the widget on screen</td>
                      </tr>
                      <tr className="border-b border-gray-100 dark:border-gray-700">
                        <td className="py-3 px-4 font-mono text-sm">primaryColor</td>
                        <td className="py-3 px-4 text-sm">string</td>
                        <td className="py-3 px-4 text-sm">{"'#4DB8B8'"}</td>
                        <td className="py-3 px-4 text-sm">Custom primary color (hex)</td>
                      </tr>
                      <tr className="border-b border-gray-100 dark:border-gray-700">
                        <td className="py-3 px-4 font-mono text-sm">defaultOpen</td>
                        <td className="py-3 px-4 text-sm">boolean</td>
                        <td className="py-3 px-4 text-sm">false</td>
                        <td className="py-3 px-4 text-sm">Initial open state</td>
                      </tr>
                      <tr className="border-b border-gray-100 dark:border-gray-700">
                        <td className="py-3 px-4 font-mono text-sm">title</td>
                        <td className="py-3 px-4 text-sm">string</td>
                        <td className="py-3 px-4 text-sm">{"'Vecinita'"}</td>
                        <td className="py-3 px-4 text-sm">Custom widget title</td>
                      </tr>
                      <tr className="border-b border-gray-100 dark:border-gray-700">
                        <td className="py-3 px-4 font-mono text-sm">customWelcomeMessage</td>
                        <td className="py-3 px-4 text-sm">string</td>
                        <td className="py-3 px-4 text-sm">undefined</td>
                        <td className="py-3 px-4 text-sm">Override default welcome message</td>
                      </tr>
                      <tr className="border-b border-gray-100 dark:border-gray-700">
                        <td className="py-3 px-4 font-mono text-sm">themeMode</td>
                        <td className="py-3 px-4 text-sm">{"'light' | 'dark' | 'auto'"}</td>
                        <td className="py-3 px-4 text-sm">{"'auto'"}</td>
                        <td className="py-3 px-4 text-sm">Theme preference</td>
                      </tr>
                      <tr>
                        <td className="py-3 px-4 font-mono text-sm">zIndex</td>
                        <td className="py-3 px-4 text-sm">number</td>
                        <td className="py-3 px-4 text-sm">1000</td>
                        <td className="py-3 px-4 text-sm">z-index for widget layering</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* The actual chat widget - see it in action! */}
            <ChatWidget
              position="bottom-right"
              primaryColor="#4DB8B8"
              defaultOpen={false}
              themeMode="auto"
              zIndex={1000}
            />
          </div>
        </BackendSettingsProvider>
      </AccessibilityProvider>
    </LanguageProvider>
  );
}
