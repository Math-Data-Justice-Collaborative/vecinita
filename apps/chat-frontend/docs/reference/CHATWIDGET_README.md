# ChatWidget Component - Plug & Play Guide

The **ChatWidget** is a fully self-contained, embeddable chat component that can be dropped into any page of your application. It includes all the features of the full Vecinita chatbot in a compact, floating widget format.

## Features

✅ **Plug & Play** - Drop it into any page with minimal setup  
✅ **Bilingual** - Full Spanish and English support  
✅ **Accessible** - Screen reader, dyslexic fonts, high contrast, highlighter mode  
✅ **Customizable** - Colors, position, theme, messages  
✅ **Responsive** - Works on mobile and desktop  
✅ **Self-Contained** - Manages its own state independently  
✅ **Source Citations** - RAG-powered responses with source links  
✅ **Markdown Answers** - Assistant responses render markdown safely  
✅ **Feedback System** - Users can rate responses  

---

## Quick Start

### 1. Basic Usage

```tsx
import { ChatWidget } from './components/ChatWidget';
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
            <h1>Welcome to My Site</h1>
            <p>Your content here...</p>
            
            {/* Add the chat widget */}
            <ChatWidget />
          </div>
        </BackendSettingsProvider>
      </AccessibilityProvider>
    </LanguageProvider>
  );
}
```

### 2. With Custom Configuration

```tsx
<ChatWidget 
  position="bottom-right"           // Widget position
  primaryColor="#FF6B6B"             // Custom brand color
  defaultOpen={false}                // Start closed
  title="Help Assistant"             // Custom title
  customWelcomeMessage="Hello! How can I help you today?"
  themeMode="dark"                   // Force dark theme
  zIndex={9999}                      // Custom z-index
/>
```

---

## Props Reference

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `position` | `'bottom-right'` \| `'bottom-left'` \| `'top-right'` \| `'top-left'` | `'bottom-right'` | Screen position of the widget |
| `primaryColor` | `string` | `'#4DB8B8'` | Primary color (hex format) for widget header and buttons |
| `defaultOpen` | `boolean` | `false` | Whether the widget starts in open state |
| `customWelcomeMessage` | `string` | `undefined` | Override the default welcome message |
| `title` | `string` | `'Vecinita'` | Title shown in widget header |
| `themeMode` | `'light'` \| `'dark'` \| `'auto'` | `'auto'` | Theme mode ('auto' allows user to toggle) |
| `zIndex` | `number` | `1000` | CSS z-index for layering |

---

## Positioning Examples

```tsx
// Bottom Right (default)
<ChatWidget position="bottom-right" />

// Bottom Left
<ChatWidget position="bottom-left" />

// Top Right
<ChatWidget position="top-right" />

// Top Left
<ChatWidget position="top-left" />
```

---

## Customization Examples

### Brand Colors

```tsx
// Custom brand colors
<ChatWidget primaryColor="#9333EA" />  // Purple
<ChatWidget primaryColor="#DC2626" />  // Red
<ChatWidget primaryColor="#059669" />  // Green
```

### Multiple Widgets (Different Purposes)

```tsx
function MyApp() {
  return (
    <LanguageProvider>
      <AccessibilityProvider>
        <BackendSettingsProvider>
          <div>
            {/* Main support widget */}
            <ChatWidget 
              position="bottom-right"
              primaryColor="#4DB8B8"
              title="Customer Support"
            />
            
            {/* Sales widget */}
            <ChatWidget 
              position="bottom-left"
              primaryColor="#9333EA"
              title="Sales Assistant"
              customWelcomeMessage="Hi! Interested in our products?"
            />
          </div>
        </BackendSettingsProvider>
      </AccessibilityProvider>
    </LanguageProvider>
  );
}
```

### Force Open on Load

```tsx
// Useful for embedded help pages
<ChatWidget defaultOpen={true} />
```

---

## Integration with Existing Apps

### React App

```tsx
// In your main App.tsx or layout component
import { ChatWidget } from './components/ChatWidget';

function App() {
  return (
    <LanguageProvider>
      <AccessibilityProvider>
        <BackendSettingsProvider>
          <YourRouter>
            {/* Your routes */}
          </YourRouter>
          
          {/* Widget appears on all pages */}
          <ChatWidget position="bottom-right" />
        </BackendSettingsProvider>
      </AccessibilityProvider>
    </LanguageProvider>
  );
}
```

### Next.js (App Router)

```tsx
// app/layout.tsx
import { ChatWidget } from '@/components/ChatWidget';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <LanguageProvider>
          <AccessibilityProvider>
            <BackendSettingsProvider>
              {children}
              <ChatWidget />
            </BackendSettingsProvider>
          </AccessibilityProvider>
        </LanguageProvider>
      </body>
    </html>
  );
}
```

### Next.js (Pages Router)

```tsx
// pages/_app.tsx
import { ChatWidget } from '@/components/ChatWidget';

function MyApp({ Component, pageProps }) {
  return (
    <LanguageProvider>
      <AccessibilityProvider>
        <BackendSettingsProvider>
          <Component {...pageProps} />
          <ChatWidget />
        </BackendSettingsProvider>
      </AccessibilityProvider>
    </LanguageProvider>
  );
}
```

---

## Features Included

### 1. Bilingual Support
- Automatic Spanish/English switching
- Language selector in widget header
- All UI elements translated

### 2. Accessibility Features
- **Screen Reader**: Text-to-speech for messages
- **Dyslexic Font**: Special font for improved readability
- **High Contrast Mode**: Enhanced contrast for visibility
- **Highlighter Mode**: Highlight text on hover
- **Reduce Motion**: Minimize animations
- **Font Size Control**: Adjust text size

### 3. Theme Support
- Light mode
- Dark mode
- Auto mode (user preference)
- Persists across sessions

### 4. User Feedback
- Rate responses (thumbs up/down)
- Add comments to feedback
- Feedback stored in localStorage

### 5. Source Citations
- Responses include source links
- Expandable source cards
- RAG-powered responses

---

## Styling & Customization

### CSS Variables

The widget respects your theme's CSS variables. You can override them:

```css
:root {
  --widget-primary: #4DB8B8;
  --background: #ffffff;
  --foreground: #000000;
  --border: rgba(0, 0, 0, 0.1);
  /* ... other variables */
}
```

### Custom Styles

Target the widget with CSS if needed:

```css
/* Adjust widget size on mobile */
@media (max-width: 640px) {
  .chat-widget {
    width: calc(100vw - 2rem);
  }
}
```

---

## State Management

The widget manages its own state independently:
- Messages are stored in component state
- Theme preference saved to `localStorage` (key: `vecinita-widget-theme`)
- Feedback saved to `localStorage` (key: `vecinita_widget_feedback`)
- Accessibility settings shared via context
- Language preference shared via context

---

## Browser Compatibility

- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

**Note**: Screen reader feature requires Web Speech API support (most modern browsers).

---

## Best Practices

### 1. Context Providers
Always wrap the widget in the required context providers:
```tsx
<LanguageProvider>
  <AccessibilityProvider>
    <BackendSettingsProvider>
      <ChatWidget />
    </BackendSettingsProvider>
  </AccessibilityProvider>
</LanguageProvider>
```

### 2. Single Instance
Use only one widget per position to avoid overlap.

### 3. Z-Index Management
If you have other floating elements (modals, tooltips), adjust `zIndex` prop:
```tsx
<ChatWidget zIndex={9999} />
```

### 4. Custom Colors
Use hex colors for `primaryColor`:
```tsx
<ChatWidget primaryColor="#FF6B6B" /> // ✅ Good
<ChatWidget primaryColor="red" />     // ❌ May not work
```

---

## Troubleshooting

### Widget Not Appearing
- Ensure context providers are wrapping the component
- Check z-index conflicts with other elements
- Verify the component is rendered in the DOM

### Theme Not Working
- Make sure CSS variables are defined in your theme
- Check that theme.css is imported
- Verify localStorage is available

### Language Not Switching
- Confirm LanguageProvider is wrapping the component
- Check that translations are loaded
- Verify localStorage access

### Accessibility Features Not Working
- Ensure AccessibilityProvider is present
- Check browser support for Web Speech API (screen reader)
- Verify CSS classes are applied correctly

---

## Examples

See the demo page at `/src/app/pages/WidgetDemo.tsx` for a complete working example with all customization options.

---

## License

This component is part of the Vecinita project.
