import { shapeArabicWordTiles } from "./arabicWordTiles";

describe("Arabic letter connections in V2 word-building tiles", () => {
  it.each([
    [["ك", "ر", "ة"], ["كـ", "ـر", "ة"]], // كُرَة: ر breaks the join before ة
    [["ش", "م", "س"], ["شـ", "ـمـ", "ـس"]],
    [["ق", "ل", "م"], ["قـ", "ـلـ", "ـم"]],
    [["ك", "ت", "ا", "ب"], ["كـ", "ـتـ", "ـا", "ب"]],
    [["ب", "ا", "ب"], ["بـ", "ـا", "ب"]], // alif does not join following baa
    [["ن", "خ", "ل", "ة"], ["نـ", "ـخـ", "ـلـ", "ـة"]],
    [["مَ", "دْ"], ["مَـ", "ـدْ"]], // preserve vowel marks with their letters
    [["ر", "و", "ز"], ["ر", "و", "ز"]], // all three break forward joining
    [["ء", "ب"], ["ء", "ب"]], // bare hamza never joins
    [["ب", "ب"], ["بـ", "ـب"]], // duplicate letters stay independent tiles
  ])("shapes separate tile letters contextually without adding an invalid join: %j", (input, expected) => {
    expect(shapeArabicWordTiles(input)).toEqual(expected);
  });

  it("preserves multi-letter fragments, sentence words, punctuation and original input", () => {
    const tiles = ["ك", "تاب", "!", "دَرْسٌ"];
    expect(shapeArabicWordTiles(tiles)).toEqual(tiles);
    expect(tiles).toEqual(["ك", "تاب", "!", "دَرْسٌ"]);
  });

  it("reacts to the child's current selection instead of memorizing a secret correct order", () => {
    const first = ["ك", "ر"];
    expect(shapeArabicWordTiles(first)).toEqual(["كـ", "ـر"]);
    expect(shapeArabicWordTiles([...first, "ة"])).toEqual(["كـ", "ـر", "ة"]);
    expect(shapeArabicWordTiles(["ر", "ك", "ة"])).toEqual(["ر", "كـ", "ـة"]);
  });
});
