const std = @import("std");
const command_tools = @import("command_tools.zig");
const Io = std.Io;

pub fn ensureWorkspace(io: Io, workspace: []const u8) !void {
    var buf: [std.fs.max_path_bytes]u8 = undefined;
    const manage = try std.fmt.bufPrint(&buf, "{s}/manage.py", .{workspace});
    if (Io.Dir.accessAbsolute(io, manage, .{})) |_| {
        return;
    } else |_| {
        return error.MissingManagePy;
    }
}

pub fn pathExists(io: Io, path: []const u8) bool {
    Io.Dir.accessAbsolute(io, path, .{}) catch return false;
    return true;
}

pub fn writeFile(io: Io, path: []const u8, contents: []const u8) !void {
    const dir_name = std.fs.path.dirname(path) orelse ".";
    try Io.Dir.cwd().createDirPath(io, dir_name);
    var file = try Io.Dir.createFileAbsolute(io, path, .{ .truncate = true });
    defer file.close(io);
    var buffer: [4096]u8 = undefined;
    var writer = file.writer(io, &buffer);
    try writer.interface.writeAll(contents);
    try writer.interface.flush();
}

pub fn runGitApply(
    allocator: std.mem.Allocator,
    io: Io,
    workspace: []const u8,
    patch_path: []const u8,
) !command_tools.CommandResult {
    return command_tools.run(allocator, io, workspace, &.{
        "git",
        "apply",
        "--whitespace=nowarn",
        patch_path,
    });
}

pub fn runGitDiff(
    allocator: std.mem.Allocator,
    io: Io,
    workspace: []const u8,
) !command_tools.CommandResult {
    return command_tools.run(allocator, io, workspace, &.{
        "git",
        "--no-pager",
        "diff",
    });
}
