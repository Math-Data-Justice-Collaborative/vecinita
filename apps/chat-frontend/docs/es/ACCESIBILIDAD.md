# Guía de Accesibilidad - Vecinita RAG Chatbot

Este documento describe todas las características de accesibilidad y comandos de teclado disponibles en la aplicación Vecinita.

## 🎯 Características de Accesibilidad

### ✅ Navegación por Teclado Completa

Todos los elementos interactivos son accesibles mediante teclado sin necesidad de ratón.

### ✅ Atajos de Teclado Globales

| Atajo | Descripción |
|-------|-------------|
| `Ctrl` + `/` | Abrir búsqueda |
| `Ctrl` + `K` | Abrir comandos |
| `Ctrl` + `N` | Nueva conversación |
| `Ctrl` + `Shift` + `H` | Ver/Ocultar historial |
| `Ctrl` + `Shift` + `S` | Abrir configuración |
| `Enter` | Enviar mensaje |
| `Shift` + `Enter` | Nueva línea en el mensaje |
| `Escape` | Cerrar modal/panel abierto |
| `Tab` | Navegar al siguiente elemento |
| `Shift` + `Tab` | Navegar al elemento anterior |
| `?` | Mostrar ayuda de atajos de teclado |

### ✅ Navegación en Listas

| Tecla | Acción |
|-------|--------|
| `↑` | Elemento anterior |
| `↓` | Elemento siguiente |
| `Home` | Primer elemento |
| `End` | Último elemento |
| `Enter` o `Espacio` | Seleccionar elemento |

### ✅ Saltar al Contenido

- Presiona `Tab` al cargar la página para activar el enlace "Saltar al contenido principal"
- Esto te lleva directamente al área de chat, evitando la navegación por el encabezado

### ✅ Lectores de Pantalla

#### Regiones ARIA
- `role="main"` en el área principal de chat
- `role="dialog"` en modales y paneles
- `role="status"` para indicadores de carga
- `aria-live="polite"` para actualizaciones dinámicas

#### Etiquetas Descriptivas
- Todos los botones tienen `aria-label`
- Los campos de formulario tienen etiquetas asociadas
- Los estados se anuncian apropiadamente

#### Contenido Oculto Visualmente
- Texto descriptivo para iconos
- Etiquetas de formularios ocultas pero accesibles
- Mensajes de estado para lectores de pantalla

### ✅ Gestión de Foco

#### Trampas de Foco
- Los modales y diálogos atrapan el foco
- `Tab` cicla dentro del modal abierto
- Al cerrar, el foco regresa al elemento que lo abrió

#### Indicadores de Foco Visibles
- Anillos de enfoque de 2px en color primario (#4DB8B8)
- Alto contraste en modo de alto contraste
- Nunca se oculta el indicador de foco

### ✅ Opciones de Tema

#### Modo Oscuro/Claro
- Toggle en el encabezado
- Respeta las preferencias del sistema
- Mantiene contraste adecuado

#### Alto Contraste
- Disponible en Panel de Accesibilidad
- Cumple con WCAG AAA
- Bordes más gruesos y colores más saturados

### ✅ Opciones de Tipografía

#### Tamaños de Fuente
- **Pequeño**: 14px
- **Mediano** (predeterminado): 16px  
- **Grande**: 18px
- **Extra Grande**: 20px

#### Familias de Fuente
- **Sans Serif** (predeterminado): Fácil de leer en pantalla
- **Serif**: Para preferencia tradicional
- **Monospace**: Para usuarios con dislexia

### ✅ Movimiento Reducido

#### Respeta preferencias del sistema
```css
@media (prefers-reduced-motion: reduce) {
  /* Todas las animaciones se reducen o eliminan */
}
```

#### Control manual
- Opción en Panel de Accesibilidad
- Desactiva transiciones suaves
- Elimina animaciones de carga

## 🔧 Panel de Accesibilidad

### Cómo Acceder
1. Presiona `Ctrl` + `Shift` + `S`, o
2. Haz clic en el ícono de Settings (⚙️) en el encabezado

### Opciones Disponibles

#### Tema
- **Claro**: Fondo blanco, texto oscuro
- **Oscuro**: Fondo oscuro, texto claro
- **Alto Contraste**: Máximo contraste para visibilidad

#### Tamaño de Fuente
- Ajustable de Pequeño a Extra Grande
- Afecta todo el texto de la aplicación
- Se guarda en localStorage

#### Familia de Fuente
- Sans Serif (predeterminado)
- Serif
- Monospace (recomendado para dislexia)

#### Reducir Movimiento
- ✅ Activado: Sin animaciones
- ❌ Desactivado: Animaciones normales

## 📱 Accesibilidad Móvil

### Gestos
- **Deslizar desde el borde izquierdo**: Abrir historial
- **Tap en menú hamburguesa**: Toggle historial
- **Double tap**: Activar elemento enfocado

### Zoom
- Soporta zoom hasta 200% sin pérdida de funcionalidad
- Los elementos se redimensionan apropiadamente
- El texto nunca se corta

### Orientación
- Funciona en orientación vertical y horizontal
- El diseño se adapta automáticamente

## ♿ Cumplimiento WCAG

Esta aplicación cumple con las Pautas de Accesibilidad para el Contenido Web (WCAG) 2.1:

### Nivel AA ✅
- [x] Contraste de color mínimo de 4.5:1
- [x] Todo el contenido accesible por teclado
- [x] Los enlaces y botones son distinguibles
- [x] El formulario tiene etiquetas
- [x] Los estados de foco son visibles
- [x] El contenido es responsive

### Nivel AAA (parcial) ✅
- [x] Contraste de color de 7:1 en modo alto contraste
- [x] Navegación consistente
- [x] Identificación de errores clara
- [x] Ayuda contextual disponible

## 🧪 Pruebas de Accesibilidad

### Herramientas Recomendadas

#### Lectores de Pantalla
- **NVDA** (Windows) - Gratuito
- **JAWS** (Windows) - Comercial
- **VoiceOver** (macOS/iOS) - Integrado
- **TalkBack** (Android) - Integrado

#### Extensiones de Navegador
- **axe DevTools** - Pruebas automatizadas
- **WAVE** - Evaluación visual
- **Lighthouse** - Auditoría de Chrome

#### Pruebas de Teclado
1. Desconecta el ratón
2. Navega usando solo `Tab`, `Enter`, y `Escape`
3. Verifica que puedas:
   - Enviar mensajes
   - Abrir configuración
   - Cerrar modales
   - Cambiar idioma
   - Ver historial

### Checklist de Pruebas

- [ ] Navegación completa con teclado
- [ ] Todos los botones tienen etiquetas
- [ ] El foco es visible en todos los elementos
- [ ] Los modales atrapan el foco
- [ ] El lector de pantalla anuncia cambios
- [ ] El contraste cumple WCAG AA
- [ ] Funciona con zoom al 200%
- [ ] Responde a preferencias de movimiento reducido

## 🎨 Personalización para Usuarios

### Guardar Preferencias

Todas las configuraciones se guardan automáticamente en `localStorage`:

```javascript
{
  "theme": "dark",
  "fontSize": "large",
  "fontFamily": "sans-serif",
  "reducedMotion": true,
  "highContrast": false,
  "language": "es"
}
```

### Restablecer Configuración

Para volver a los valores predeterminados:
1. Abre Panel de Accesibilidad
2. (Opcional en futuras versiones: botón "Restablecer")
3. O limpia localStorage del navegador

## 📞 Soporte

### Reportar Problemas de Accesibilidad

Si encuentras barreras de accesibilidad:

1. **GitHub Issues**: Crea un issue con la etiqueta `accessibility`
2. **Email**: [Agregar email de soporte]
3. **Incluye**:
   - Descripción del problema
   - Navegador y versión
   - Tecnología asistiva utilizada
   - Pasos para reproducir

### Solicitar Mejoras

Siempre estamos mejorando la accesibilidad. Sugerencias bienvenidas!

## 📚 Recursos Adicionales

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [MDN Accessibility](https://developer.mozilla.org/es/docs/Web/Accessibility)
- [WebAIM](https://webaim.org/)
- [A11y Project](https://www.a11yproject.com/)

## 🌟 Mejores Prácticas para Usuarios

### Para Usuarios de Lectores de Pantalla
1. Usa el enlace "Saltar al contenido" (`Tab` al inicio)
2. Los mensajes nuevos se anuncian automáticamente
3. El estado de carga se anuncia durante las respuestas

### Para Usuarios de Solo Teclado
1. Presiona `?` para ver todos los atajos disponibles
2. Usa `Tab` para navegar secuencialmente
3. Usa atajos de teclado para acceso rápido

### Para Usuarios con Baja Visión
1. Aumenta el tamaño de fuente en Panel de Accesibilidad
2. Activa Modo de Alto Contraste
3. Usa zoom del navegador (Ctrl + + / Ctrl + -)

### Para Usuarios con Sensibilidad al Movimiento
1. Activa "Reducir Movimiento" en Panel de Accesibilidad
2. O configura tu sistema operativo para reducir movimiento
3. La aplicación respetará tu preferencia automáticamente

---

**Última actualización**: Enero 2026  
**Versión**: 1.0
