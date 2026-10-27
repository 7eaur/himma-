import { fileURLToPath } from "node:url";

const stripRuntimeGoogleFontsPlugin = fileURLToPath(
  new URL("./postcss-strip-google-fonts.cjs", import.meta.url),
);

const config = {
  plugins: {
    [stripRuntimeGoogleFontsPlugin]: {},
    "@tailwindcss/postcss": {},
  },
};

export default config;
