const std = @import("std");
const Io = std.Io;
const command_tools = @import("command_tools.zig");

pub const ValidationMatrix = struct {
    forms_present: bool,
    admin_present: bool,
    migration_present: bool,
    targeted_test_present: bool,
    serializer_present: bool,
    model_present: bool,

    pub fn allPassed(self: ValidationMatrix) bool {
        return self.forms_present and
            self.admin_present and
            self.migration_present and
            self.targeted_test_present and
            self.serializer_present and
            self.model_present;
    }
};

fn fileContains(allocator: std.mem.Allocator, io: Io, cwd: []const u8, file_path: []const u8, needle: []const u8) !bool {
    const result = try command_tools.run(allocator, io, cwd, &.{
        "python3",
        "-c",
        "from pathlib import Path; import sys; sys.exit(0 if sys.argv[2] in Path(sys.argv[1]).read_text(encoding='utf-8') else 1)",
        file_path,
        needle,
    });
    defer allocator.free(result.stdout);
    defer allocator.free(result.stderr);
    return command_tools.succeeded(result.term);
}

pub fn runStatic(allocator: std.mem.Allocator, io: Io, workspace: []const u8) !ValidationMatrix {
    return .{
        .forms_present = try fileContains(allocator, io, workspace, "files/forms.py", "content_warning"),
        .admin_present = try fileContains(allocator, io, workspace, "files/admin.py", "content_warning"),
        .migration_present = try fileContains(allocator, io, workspace, "files/migrations/0015_media_content_warning.py", "content_warning"),
        .targeted_test_present = try fileContains(allocator, io, workspace, "tests/api/test_content_warning.py", "content_warning"),
        .serializer_present = try fileContains(allocator, io, workspace, "files/serializers.py", "content_warning"),
        .model_present = try fileContains(allocator, io, workspace, "files/models/media.py", "content_warning"),
    };
}
