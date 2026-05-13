/**
 * VECINITA CHAT WIDGET - USAGE EXAMPLES
 *
 * This file shows various ways to use the ChatWidget component
 * Copy and paste these examples into your own application
 */

import { useState } from 'react';
import { ChatWidget } from '../app/components/ChatWidget';
import { LanguageProvider } from '../app/context/LanguageContext';
import { AccessibilityProvider } from '../app/context/AccessibilityContext';
import { BackendSettingsProvider } from '../app/context/BackendSettingsContext';

// ============================================
// EXAMPLE 1: Basic Usage (Minimal Setup)
// ============================================
export function BasicExample() {
  return (
    <LanguageProvider>
      <AccessibilityProvider>
        <BackendSettingsProvider>
          <div>
            <h1>My Website</h1>
            <p>Your content here...</p>

            {/* Minimal widget - uses all defaults */}
            <ChatWidget />
          </div>
        </BackendSettingsProvider>
      </AccessibilityProvider>
    </LanguageProvider>
  );
}

// ============================================
// EXAMPLE 2: Custom Brand Colors
// ============================================
export function BrandedExample() {
  return (
    <LanguageProvider>
      <AccessibilityProvider>
        <BackendSettingsProvider>
          <div>
            <h1>ACME Corporation</h1>

            {/* Widget with custom purple brand color */}
            <ChatWidget
              primaryColor="#9333EA"
              title="ACME Support"
              customWelcomeMessage="Welcome to ACME! How can we help you today?"
            />
          </div>
        </BackendSettingsProvider>
      </AccessibilityProvider>
    </LanguageProvider>
  );
}

// ============================================
// EXAMPLE 3: Different Positions
// ============================================
export function PositionExamples() {
  return (
    <LanguageProvider>
      <AccessibilityProvider>
        <BackendSettingsProvider>
          <div>
            {/* Bottom Right (default) */}
            <ChatWidget position="bottom-right" />

            {/* Bottom Left */}
            <ChatWidget position="bottom-left" primaryColor="#DC2626" />

            {/* Top Right */}
            <ChatWidget position="top-right" primaryColor="#059669" />

            {/* Top Left */}
            <ChatWidget position="top-left" primaryColor="#F59E0B" />
          </div>
        </BackendSettingsProvider>
      </AccessibilityProvider>
    </LanguageProvider>
  );
}

// ============================================
// EXAMPLE 4: Start Open (e.g., Help Pages)
// ============================================
export function HelpPageExample() {
  return (
    <LanguageProvider>
      <AccessibilityProvider>
        <BackendSettingsProvider>
          <div>
            <h1>Help Center</h1>
            <p>Browse our help articles or chat with us below.</p>

            {/* Widget starts open */}
            <ChatWidget defaultOpen={true} title="Help Assistant" />
          </div>
        </BackendSettingsProvider>
      </AccessibilityProvider>
    </LanguageProvider>
  );
}

// ============================================
// EXAMPLE 5: Multiple Widgets (Different Purposes)
// ============================================
export function MultiWidgetExample() {
  return (
    <LanguageProvider>
      <AccessibilityProvider>
        <BackendSettingsProvider>
          <div>
            <h1>E-Commerce Store</h1>

            {/* Support widget - bottom right */}
            <ChatWidget
              position="bottom-right"
              primaryColor="#4DB8B8"
              title="Customer Support"
              customWelcomeMessage="Need help with your order?"
            />

            {/* Sales widget - bottom left */}
            <ChatWidget
              position="bottom-left"
              primaryColor="#9333EA"
              title="Sales Chat"
              customWelcomeMessage="Hi! Interested in our products? Let's chat!"
              zIndex={999}
            />
          </div>
        </BackendSettingsProvider>
      </AccessibilityProvider>
    </LanguageProvider>
  );
}

// ============================================
// EXAMPLE 6: Dark Theme Only
// ============================================
export function DarkThemeExample() {
  return (
    <LanguageProvider>
      <AccessibilityProvider>
        <BackendSettingsProvider>
          <div className="bg-gray-900 min-h-screen">
            <h1 className="text-white">Dark Mode Website</h1>

            {/* Force dark theme */}
            <ChatWidget themeMode="dark" primaryColor="#60A5FA" />
          </div>
        </BackendSettingsProvider>
      </AccessibilityProvider>
    </LanguageProvider>
  );
}

// ============================================
// EXAMPLE 7: React Router Integration
// ============================================
import { BrowserRouter, Routes, Route } from 'react-router-dom';

export function RouterExample() {
  return (
    <LanguageProvider>
      <AccessibilityProvider>
        <BackendSettingsProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/about" element={<AboutPage />} />
              <Route path="/contact" element={<ContactPage />} />
            </Routes>

            {/* Widget appears on ALL pages */}
            <ChatWidget position="bottom-right" />
          </BrowserRouter>
        </BackendSettingsProvider>
      </AccessibilityProvider>
    </LanguageProvider>
  );
}

// Dummy page components
function HomePage() {
  return (
    <div>
      <h1>Home</h1>
    </div>
  );
}

function AboutPage() {
  return (
    <div>
      <h1>About</h1>
    </div>
  );
}

function ContactPage() {
  return (
    <div>
      <h1>Contact</h1>
    </div>
  );
}

// ============================================
// EXAMPLE 8: Conditional Widget (Logged-in Users Only)
// ============================================
export function ConditionalExample() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  return (
    <LanguageProvider>
      <AccessibilityProvider>
        <BackendSettingsProvider>
          <div>
            <h1>Members Area</h1>
            <button onClick={() => setIsLoggedIn(!isLoggedIn)}>
              {isLoggedIn ? 'Log Out' : 'Log In'}
            </button>

            {/* Only show widget when logged in */}
            {isLoggedIn && (
              <ChatWidget
                title="Member Support"
                customWelcomeMessage="Welcome back! How can we assist you today?"
              />
            )}
          </div>
        </BackendSettingsProvider>
      </AccessibilityProvider>
    </LanguageProvider>
  );
}

// ============================================
// EXAMPLE 9: Custom Z-Index (Above Modals)
// ============================================
export function ZIndexExample() {
  const [showModal, setShowModal] = useState(false);

  return (
    <LanguageProvider>
      <AccessibilityProvider>
        <BackendSettingsProvider>
          <div>
            <button onClick={() => setShowModal(true)}>Open Modal</button>

            {/* Modal with z-index 500 */}
            {showModal && (
              <div
                className="fixed inset-0 bg-black/50 flex items-center justify-center"
                style={{ zIndex: 500 }}
                onClick={() => setShowModal(false)}
              >
                <div className="bg-white p-8 rounded-lg">
                  <h2>Modal Content</h2>
                  <button onClick={() => setShowModal(false)}>Close</button>
                </div>
              </div>
            )}

            {/* Widget appears ABOVE modal (higher z-index) */}
            <ChatWidget zIndex={1000} />
          </div>
        </BackendSettingsProvider>
      </AccessibilityProvider>
    </LanguageProvider>
  );
}

// ============================================
// EXAMPLE 10: Embedding in WordPress/Static HTML
// ============================================
/*
 * For WordPress or static HTML sites, you'll need to:
 *
 * 1. Build the React component as a standalone bundle
 * 2. Include the bundle in your HTML
 * 3. Mount it to a div
 *
 * Example HTML:
 *
 * <div id="vecinita-widget"></div>
 * <script src="vecinita-widget.bundle.js"></script>
 * <script>
 *   VecinitatWidget.mount('#vecinita-widget', {
 *     position: 'bottom-right',
 *     primaryColor: '#4DB8B8'
 *   });
 * </script>
 */

// ============================================
// QUICK REFERENCE - All Available Props
// ============================================
/*
<ChatWidget 
  position="bottom-right" | "bottom-left" | "top-right" | "top-left"
  primaryColor="#4DB8B8"          // Hex color
  defaultOpen={false}             // boolean
  customWelcomeMessage="Hello!"   // string
  title="Vecinita"                // string
  themeMode="auto" | "light" | "dark"
  zIndex={1000}                   // number
/>
*/
