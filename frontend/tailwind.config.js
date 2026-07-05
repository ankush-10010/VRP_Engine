/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      "colors": {
              "surface-container-high": "#1f2b38",
              "error": "#ffb4ab",
              "on-surface": "#d7e3f5",
              "on-primary-fixed-variant": "#5a4300",
              "primary-fixed": "#ffc300",
              "surface-dim": "#081421",
              "on-background": "#d7e3f5",
              "on-tertiary-container": "#665500",
              "surface-tint": "#ffc300",
              "on-secondary-container": "#95baf3",
              "on-secondary": "#00315f",
              "on-tertiary": "#3b2f00",
              "surface-bright": "#2e3a48",
              "primary": "#ffc300",
              "on-error-container": "#ffdad6",
              "inverse-surface": "#d7e3f5",
              "surface": "#000814",
              "surface-container-highest": "#2a3643",
              "background": "#000814",
              "secondary-fixed-dim": "#a5c8ff",
              "inverse-on-surface": "#26313f",
              "inverse-primary": "#785a00",
              "secondary-fixed": "#d4e3ff",
              "surface-container-low": "#101c29",
              "on-secondary-fixed": "#001c3a",
              "tertiary-fixed-dim": "#e9c400",
              "on-primary-fixed": "#251a00",
              "on-tertiary-fixed-variant": "#554600",
              "error-container": "#93000a",
              "secondary-container": "#214a7c",
              "secondary": "#a5c8ff",
              "primary-container": "#ffc300",
              "outline-variant": "#4f4632",
              "surface-container": "#001D3D",
              "tertiary-container": "#f0c900",
              "on-secondary-fixed-variant": "#1e4879",
              "tertiary": "#ffe795",
              "on-primary-container": "#6d5200",
              "surface-variant": "#2a3643",
              "on-primary": "#3f2e00",
              "tertiary-fixed": "#ffe171",
              "on-tertiary-fixed": "#221b00",
              "on-error": "#690005",
              "primary-fixed-dim": "#ffc300",
              "on-surface-variant": "#ffc300",
              "surface-container-lowest": "#040f1b",
              "outline": "#9c8f78"
      },
      "borderRadius": {
              "DEFAULT": "0.125rem",
              "lg": "0.25rem",
              "xl": "0.5rem",
              "full": "0.75rem"
      },
      "spacing": {
              "stack-md": "16px",
              "stack-lg": "32px",
              "gutter": "16px",
              "unit": "4px",
              "stack-sm": "8px",
              "container-padding": "12px",
              "margin-page": "24px",
              "max-width": "1440px",
              "margin-mobile": "16px",
              "margin-desktop": "32px",
              "container-max": "1440px"
      },
      "fontFamily": {
              "headline-lg-mobile": [
                      "Geist"
              ],
              "label-xs": [
                      "JetBrains Mono"
              ],
              "headline-xl": [
                      "Geist"
              ],
              "body-md": [
                      "Geist"
              ],
              "headline-lg": [
                      "Geist"
              ],
              "code-sm": [
                      "JetBrains Mono"
              ],
              "data-display": [
                      "JetBrains Mono"
              ],
              "label-caps": [
                      "JetBrains Mono"
              ],
              "body-sm": [
                      "Geist"
              ],
              "headline-md": [
                      "Geist"
              ],
              "label-mono-md": [
                      "JetBrains Mono"
              ],
              "headline-sm": [
                      "Geist"
              ],
              "label-mono-lg": [
                      "JetBrains Mono"
              ],
              "label-mono-sm": [
                      "JetBrains Mono"
              ],
              "body-lg": [
                      "Geist"
              ]
      },
      "fontSize": {
              "headline-lg-mobile": [
                      "24px",
                      {
                              "lineHeight": "32px",
                              "fontWeight": "600"
                      }
              ],
              "label-xs": [
                      "12px",
                      {
                              "lineHeight": "16px",
                              "fontWeight": "700"
                      }
              ],
              "headline-xl": [
                      "48px",
                      {
                              "lineHeight": "56px",
                              "letterSpacing": "-0.02em",
                              "fontWeight": "700"
                      }
              ],
              "body-md": [
                      "14px",
                      {
                              "lineHeight": "1.5",
                              "fontWeight": "400"
                          }
              ],
              "headline-lg": [
                      "32px",
                      {
                              "lineHeight": "1.2",
                              "letterSpacing": "-0.02em",
                              "fontWeight": "600"
                      }
              ],
              "code-sm": [
                      "14px",
                      {
                              "lineHeight": "20px",
                              "fontWeight": "500"
                      }
              ],
              "data-display": [
                      "18px",
                      {
                              "lineHeight": "1.4",
                              "letterSpacing": "0.02em",
                              "fontWeight": "500"
                      }
              ],
              "label-caps": [
                      "12px",
                      {
                              "lineHeight": "1",
                              "letterSpacing": "0.05em",
                              "fontWeight": "700"
                      }
              ],
              "body-sm": [
                      "14px",
                      {
                              "lineHeight": "1.5",
                              "fontWeight": "400"
                      }
              ],
              "headline-md": [
                      "24px",
                      {
                              "lineHeight": "1.3",
                              "fontWeight": "600"
                      }
              ],
              "label-mono-md": [
                      "13px",
                      {
                              "lineHeight": "1.2",
                              "fontWeight": "500"
                      }
              ],
              "headline-sm": [
                      "20px",
                      {
                              "lineHeight": "1.4",
                              "fontWeight": "500"
                      }
              ],
              "label-mono-lg": [
                      "16px",
                      {
                              "lineHeight": "1.2",
                              "fontWeight": "500"
                      }
              ],
              "label-mono-sm": [
                      "11px",
                      {
                              "lineHeight": "1.2",
                              "letterSpacing": "0.05em",
                              "fontWeight": "400"
                      }
              ],
              "body-lg": [
                      "16px",
                      {
                              "lineHeight": "1.5",
                              "fontWeight": "400"
                      }
              ]
      }
    },
  },
  plugins: [],
}
