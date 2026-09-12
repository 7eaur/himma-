import tailwindcss from "@tailwindcss/postcss";

const stripRuntimeGoogleFonts = {
  postcssPlugin: "himma-strip-runtime-google-fonts",
  AtRule: {
    import(atRule) {
      if (atRule.params.includes("fonts.googleapis.com")) {
        atRule.remove();
      }
    },
  },
};

const config = {
  plugins: [stripRuntimeGoogleFonts, tailwindcss()],
};

export default config;
