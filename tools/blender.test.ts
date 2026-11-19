import { describe, expect, it } from "vitest";
import { findBlender } from "./blender.ts";

describe("findBlender", () => {
  it("prefers $BLENDER, then the macOS app, then $PATH, else nothing", () => {
    expect(findBlender({ BLENDER: "/x/blender" }, () => false)).toBe(
      "/x/blender",
    );
    expect(findBlender({}, () => true)).toMatch(/Blender\.app/);
    expect(
      findBlender({ PATH: "/usr/bin:/home/j/.local/bin" }, (path) =>
        path.startsWith("/home/j/"),
      ),
    ).toBe("/home/j/.local/bin/blender");
    expect(findBlender({ PATH: "/usr/bin" }, () => false)).toBeUndefined();
    expect(findBlender({}, () => false)).toBeUndefined();
  });
});
