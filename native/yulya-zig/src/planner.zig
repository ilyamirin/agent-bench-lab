const std = @import("std");

pub fn taskSupported(prompt: []const u8) bool {
    return std.mem.indexOf(u8, prompt, "content_warning") != null and
        std.mem.indexOf(u8, prompt, "MediaCMS") != null;
}
