// SPDX-License-Identifier: GPL-2.0-only
/*
 * Freestanding aarch64 DRM page-flip diagnostic for atom bring-up.
 *
 * This intentionally avoids libdrm and libc so it can run from the minimal
 * initramfs. It performs a legacy KMS page-flip through raw ioctls:
 *
 *   GETRESOURCES -> GETCRTC -> CREATE_DUMB -> MAP_DUMB -> mmap
 *   -> ADDFB2 -> PAGE_FLIP -> read FLIP_COMPLETE -> restore
 *
 * Build with:
 *   aarch64-linux-gnu-gcc -nostdlib -static -ffreestanding \
 *       -fno-builtin -fno-stack-protector -O2 -Wall -Wextra -Werror \
 *       -Wl,-e,_start -o drmflip tools/drmflip.c
 */

typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef unsigned long u64;
typedef long s64;

#define SYS_ioctl 29
#define SYS_openat 56
#define SYS_close 57
#define SYS_read 63
#define SYS_write 64
#define SYS_exit_group 94
#define SYS_nanosleep 101
#define SYS_mmap 222
#define SYS_munmap 215

#define AT_FDCWD -100
#define O_RDWR 2

#define PROT_READ 1
#define PROT_WRITE 2
#define MAP_SHARED 1

#define DRM_IOCTL_BASE 'd'
#define _IOC_NRBITS 8
#define _IOC_TYPEBITS 8
#define _IOC_SIZEBITS 14
#define _IOC_DIRBITS 2
#define _IOC_NRSHIFT 0
#define _IOC_TYPESHIFT 8
#define _IOC_SIZESHIFT 16
#define _IOC_DIRSHIFT 30
#define _IOC_NONE 0U
#define _IOC_WRITE 1U
#define _IOC_READ 2U
#define _IOC(dir, type, nr, size) \
	(((dir) << _IOC_DIRSHIFT) | ((type) << _IOC_TYPESHIFT) | \
	 ((nr) << _IOC_NRSHIFT) | ((size) << _IOC_SIZESHIFT))
#define DRM_IO(nr) _IOC(_IOC_NONE, DRM_IOCTL_BASE, nr, 0)
#define DRM_IOWR(nr, type) \
	_IOC(_IOC_READ | _IOC_WRITE, DRM_IOCTL_BASE, nr, sizeof(type))

#define DRM_IOCTL_SET_MASTER DRM_IO(0x1e)
#define DRM_IOCTL_DROP_MASTER DRM_IO(0x1f)

struct drm_mode_card_res {
	u64 fb_id_ptr;
	u64 crtc_id_ptr;
	u64 connector_id_ptr;
	u64 encoder_id_ptr;
	u32 count_fbs;
	u32 count_crtcs;
	u32 count_connectors;
	u32 count_encoders;
	u32 min_width;
	u32 max_width;
	u32 min_height;
	u32 max_height;
};

struct drm_mode_modeinfo {
	u32 clock;
	u16 hdisplay;
	u16 hsync_start;
	u16 hsync_end;
	u16 htotal;
	u16 hskew;
	u16 vdisplay;
	u16 vsync_start;
	u16 vsync_end;
	u16 vtotal;
	u16 vscan;
	u32 vrefresh;
	u32 flags;
	u32 type;
	char name[32];
};

struct drm_mode_crtc {
	u64 set_connectors_ptr;
	u32 count_connectors;
	u32 crtc_id;
	u32 fb_id;
	u32 x;
	u32 y;
	u32 gamma_size;
	u32 mode_valid;
	struct drm_mode_modeinfo mode;
};

struct drm_mode_create_dumb {
	u32 height;
	u32 width;
	u32 bpp;
	u32 flags;
	u32 handle;
	u32 pitch;
	u64 size;
};

struct drm_mode_map_dumb {
	u32 handle;
	u32 pad;
	u64 offset;
};

struct drm_mode_destroy_dumb {
	u32 handle;
};

struct drm_mode_fb_cmd2 {
	u32 fb_id;
	u32 width;
	u32 height;
	u32 pixel_format;
	u32 flags;
	u32 handles[4];
	u32 pitches[4];
	u32 offsets[4];
	u64 modifier[4];
};

struct drm_mode_crtc_page_flip {
	u32 crtc_id;
	u32 fb_id;
	u32 flags;
	u32 reserved;
	u64 user_data;
};

struct drm_event {
	u32 type;
	u32 length;
};

struct drm_event_vblank {
	struct drm_event base;
	u64 user_data;
	u32 tv_sec;
	u32 tv_usec;
	u32 sequence;
	u32 crtc_id;
};

struct timespec {
	s64 tv_sec;
	s64 tv_nsec;
};

#define DRM_IOCTL_MODE_GETRESOURCES \
	DRM_IOWR(0xa0, struct drm_mode_card_res)
#define DRM_IOCTL_MODE_GETCRTC DRM_IOWR(0xa1, struct drm_mode_crtc)
#define DRM_IOCTL_MODE_RMFB DRM_IOWR(0xaf, u32)
#define DRM_IOCTL_MODE_PAGE_FLIP \
	DRM_IOWR(0xb0, struct drm_mode_crtc_page_flip)
#define DRM_IOCTL_MODE_CREATE_DUMB \
	DRM_IOWR(0xb2, struct drm_mode_create_dumb)
#define DRM_IOCTL_MODE_MAP_DUMB \
	DRM_IOWR(0xb3, struct drm_mode_map_dumb)
#define DRM_IOCTL_MODE_DESTROY_DUMB \
	DRM_IOWR(0xb4, struct drm_mode_destroy_dumb)
#define DRM_IOCTL_MODE_ADDFB2 DRM_IOWR(0xb8, struct drm_mode_fb_cmd2)

#define DRM_MODE_PAGE_FLIP_EVENT 0x01
#define DRM_EVENT_FLIP_COMPLETE 0x02

#ifndef DRMFLIP_STRESS_FLIP_COUNT
#define DRMFLIP_STRESS_FLIP_COUNT 0
#endif

#define DRMFLIP_STRESS_LOG_INTERVAL 60
#define DRMFLIP_STRESS_FRAMES_PER_COLOR 120

#define fourcc_code(a, b, c, d) \
	((u32)(a) | ((u32)(b) << 8) | ((u32)(c) << 16) | ((u32)(d) << 24))
#define DRM_FORMAT_XRGB8888 fourcc_code('X', 'R', '2', '4')

static long sc1(long nr, long a)
{
	register long x8 asm("x8") = nr;
	register long x0 asm("x0") = a;

	asm volatile("svc #0" : "+r"(x0) : "r"(x8) : "memory", "cc");
	return x0;
}

static long sc3(long nr, long a, long b, long c)
{
	register long x8 asm("x8") = nr;
	register long x0 asm("x0") = a;
	register long x1 asm("x1") = b;
	register long x2 asm("x2") = c;

	asm volatile("svc #0"
		     : "+r"(x0)
		     : "r"(x8), "r"(x1), "r"(x2)
		     : "memory", "cc");
	return x0;
}

static long sc6(long nr, long a, long b, long c, long d, long e, long f)
{
	register long x8 asm("x8") = nr;
	register long x0 asm("x0") = a;
	register long x1 asm("x1") = b;
	register long x2 asm("x2") = c;
	register long x3 asm("x3") = d;
	register long x4 asm("x4") = e;
	register long x5 asm("x5") = f;

	asm volatile("svc #0"
		     : "+r"(x0)
		     : "r"(x8), "r"(x1), "r"(x2), "r"(x3), "r"(x4), "r"(x5)
		     : "memory", "cc");
	return x0;
}

static long sys_open(const char *path)
{
	return sc6(SYS_openat, AT_FDCWD, (long)path, O_RDWR, 0, 0, 0);
}

static long sys_ioctl(long fd, unsigned long request, void *arg)
{
	return sc3(SYS_ioctl, fd, (long)request, (long)arg);
}

static long sys_read(long fd, void *buf, long count)
{
	return sc3(SYS_read, fd, (long)buf, count);
}

static void sys_write(long fd, const void *buf, long count)
{
	sc3(SYS_write, fd, (long)buf, count);
}

static void sys_close(long fd)
{
	sc1(SYS_close, fd);
}

static void sys_exit(long code)
{
	sc1(SYS_exit_group, code);
}

static void sleep_seconds(long seconds)
{
	struct timespec ts;

	ts.tv_sec = seconds;
	ts.tv_nsec = 0;
	sc3(SYS_nanosleep, (long)&ts, 0, 0);
}

static u64 string_len(const char *text)
{
	u64 len = 0;

	while (text[len])
		len++;
	return len;
}

static void out(const char *text)
{
	sys_write(1, text, string_len(text));
}

static void out_u64(const char *label, u64 value)
{
	char digits[32];
	char result[96];
	u64 count = 0;
	u64 pos = 0;
	u64 i;

	while (label[pos]) {
		result[pos] = label[pos];
		pos++;
	}
	if (!value) {
		digits[count++] = '0';
	} else {
		while (value) {
			digits[count++] = '0' + (value % 10);
			value /= 10;
		}
	}
	for (i = count; i > 0; i--)
		result[pos++] = digits[i - 1];
	result[pos++] = '\n';
	sys_write(1, result, pos);
}

static void out_hex(const char *label, u64 value)
{
	static const char hex[] = "0123456789abcdef";
	char result[96];
	u64 pos = 0;
	u64 i;

	while (label[pos]) {
		result[pos] = label[pos];
		pos++;
	}
	result[pos++] = '0';
	result[pos++] = 'x';
	for (i = 16; i > 0; i--)
		result[pos++] = hex[(value >> ((i - 1) * 4)) & 0xf];
	result[pos++] = '\n';
	sys_write(1, result, pos);
}

static void out_name(const char *name)
{
	u64 len = 0;

	while (len < 32 && name[len])
		len++;
	sys_write(1, name, len);
}

static const char *err_name(long ret)
{
	switch (-ret) {
	case 1: return "EPERM";
	case 12: return "ENOMEM";
	case 13: return "EACCES";
	case 14: return "EFAULT";
	case 16: return "EBUSY";
	case 19: return "ENODEV";
	case 22: return "EINVAL";
	case 25: return "ENOTTY";
	case 38: return "ENOSYS";
	case 95: return "EOPNOTSUPP";
	case 110: return "ETIMEDOUT";
	default: return "?";
	}
}

static void out_ret(const char *what, long ret)
{
	out(what);
	if (ret < 0) {
		out(" = <err ");
		out(err_name(ret));
		out(">\n");
	} else {
		out_u64(" = ", ret);
	}
}

static long create_dumb(long fd, u32 width, u32 height,
			struct drm_mode_create_dumb *dumb)
{
	dumb->height = height;
	dumb->width = width;
	dumb->bpp = 32;
	dumb->flags = 0;
	dumb->handle = 0;
	dumb->pitch = 0;
	dumb->size = 0;
	return sys_ioctl(fd, DRM_IOCTL_MODE_CREATE_DUMB, dumb);
}

static long map_dumb(long fd, struct drm_mode_create_dumb *dumb,
		     void **mapping, u64 *offset)
{
	struct drm_mode_map_dumb map;
	long ret;

	map.handle = dumb->handle;
	map.pad = 0;
	map.offset = 0;
	ret = sys_ioctl(fd, DRM_IOCTL_MODE_MAP_DUMB, &map);
	if (ret)
		return ret;
	*mapping = (void *)sc6(SYS_mmap, 0, dumb->size,
			       PROT_READ | PROT_WRITE, MAP_SHARED, fd,
			       map.offset);
	if ((long)*mapping < 0 && (long)*mapping >= -4095)
		return (long)*mapping;
	*offset = map.offset;
	return 0;
}

static void fill_pixels(struct drm_mode_create_dumb *dumb, void *mapping,
			u32 pixel)
{
	u32 *row = (u32 *)mapping;
	u32 stride = dumb->pitch / 4;
	u32 x;
	u32 y;

	for (y = 0; y < dumb->height; y++) {
		for (x = 0; x < dumb->width; x++)
			row[x] = pixel;
		row += stride;
	}
}

static long add_fb(long fd, struct drm_mode_create_dumb *dumb,
		   u32 width, u32 height, u32 *fb_id)
{
	struct drm_mode_fb_cmd2 fb;
	u32 i;
	long ret;

	fb.fb_id = 0;
	fb.width = width;
	fb.height = height;
	fb.pixel_format = DRM_FORMAT_XRGB8888;
	fb.flags = 0;
	for (i = 0; i < 4; i++) {
		fb.handles[i] = 0;
		fb.pitches[i] = 0;
		fb.offsets[i] = 0;
		fb.modifier[i] = 0;
	}
	fb.handles[0] = dumb->handle;
	fb.pitches[0] = dumb->pitch;
	ret = sys_ioctl(fd, DRM_IOCTL_MODE_ADDFB2, &fb);
	if (!ret)
		*fb_id = fb.fb_id;
	return ret;
}

static long flip_and_wait(long fd, u32 crtc_id, u32 fb_id, u64 user_data,
			  int verbose)
{
	struct drm_mode_crtc_page_flip flip;
	union {
		struct drm_event_vblank event;
		u8 raw[256];
	} event_buf;
	long ret;
	u64 i;

	flip.crtc_id = crtc_id;
	flip.fb_id = fb_id;
	flip.flags = DRM_MODE_PAGE_FLIP_EVENT;
	flip.reserved = 0;
	flip.user_data = user_data;
	if (verbose)
		out_hex("PAGE_FLIP fb=", fb_id);
	ret = sys_ioctl(fd, DRM_IOCTL_MODE_PAGE_FLIP, &flip);
	if (ret) {
		out_ret("PAGE_FLIP submit", ret);
		return ret;
	}
	if (verbose)
		out_ret("PAGE_FLIP submit", ret);

	for (i = 0; i < 8; i++) {
		struct drm_event_vblank *event = &event_buf.event;

		ret = sys_read(fd, event_buf.raw, sizeof(event_buf.raw));
		if (ret < 0) {
			out_ret("event read", ret);
			return ret;
		}
		if (verbose)
			out_ret("event read", ret);
		if (ret < (long)sizeof(struct drm_event_vblank))
			continue;
		if (verbose) {
			out_hex("event type=", event->base.type);
			out_hex("event user=", event->user_data);
		}
		if (event->base.type == DRM_EVENT_FLIP_COMPLETE &&
		    event->user_data == user_data) {
			if (verbose)
				out_u64("event sequence=", event->sequence);
			return 0;
		}
	}
	return -110;
}

static int run(void)
{
	struct drm_mode_card_res resources;
	struct drm_mode_crtc crtc;
	struct drm_mode_create_dumb red;
	struct drm_mode_create_dumb blue;
	struct drm_mode_destroy_dumb destroy;
	u32 crtc_ids[8];
	u32 connector_ids[8];
	u32 encoder_ids[8];
	u32 fb_ids[8];
	u32 red_fb = 0;
	u32 blue_fb = 0;
	u32 current_fb;
	u32 width;
	u32 height;
	void *red_map = 0;
	void *blue_map = 0;
	u64 red_offset = 0;
	u64 blue_offset = 0;
	long fd;
	long ret;
	int status = 1;
	u32 i;
#if DRMFLIP_STRESS_FLIP_COUNT > 0
	u32 stress_index;
	u32 stress_fb;
#endif

	out("===== drmflip begin =====\n");
	fd = sys_open("/dev/dri/card0");
	if (fd < 0) {
		out_ret("open /dev/dri/card0", fd);
		return 1;
	}
	out("open /dev/dri/card0 = OK\n");

	ret = sys_ioctl(fd, DRM_IOCTL_SET_MASTER, 0);
	out_ret("SET_MASTER", ret);
	if (ret)
		goto out_close;

	for (i = 0; i < 8; i++) {
		crtc_ids[i] = 0;
		connector_ids[i] = 0;
		encoder_ids[i] = 0;
		fb_ids[i] = 0;
	}
	resources.fb_id_ptr = (u64)fb_ids;
	resources.crtc_id_ptr = (u64)crtc_ids;
	resources.connector_id_ptr = (u64)connector_ids;
	resources.encoder_id_ptr = (u64)encoder_ids;
	resources.count_fbs = 8;
	resources.count_crtcs = 8;
	resources.count_connectors = 8;
	resources.count_encoders = 8;
	resources.min_width = 0;
	resources.max_width = 0;
	resources.min_height = 0;
	resources.max_height = 0;
	ret = sys_ioctl(fd, DRM_IOCTL_MODE_GETRESOURCES, &resources);
	out_ret("GETRESOURCES", ret);
	if (ret || resources.count_crtcs < 1)
		goto out_drop_master;
	out_u64("resources crtcs=", resources.count_crtcs);
	out_u64("resources connectors=", resources.count_connectors);
	out_u64("resources encoders=", resources.count_encoders);
	out_u64("resources fbs=", resources.count_fbs);
	out_hex("first crtc id=", crtc_ids[0]);

	for (i = 0; i < sizeof(crtc); i++)
		((u8 *)&crtc)[i] = 0;
	crtc.crtc_id = crtc_ids[0];
	ret = sys_ioctl(fd, DRM_IOCTL_MODE_GETCRTC, &crtc);
	out_ret("GETCRTC", ret);
	if (ret || !crtc.mode_valid)
		goto out_drop_master;
	width = crtc.mode.hdisplay;
	height = crtc.mode.vdisplay;
	current_fb = crtc.fb_id;
	out_hex("current fb=", current_fb);
	out_u64("mode width=", width);
	out_u64("mode height=", height);
	out_u64("mode refresh=", crtc.mode.vrefresh);
	out("mode name=");
	out_name(crtc.mode.name);
	out("\n");
	if (!width || !height)
		goto out_drop_master;

	ret = create_dumb(fd, width, height, &red);
	out_ret("CREATE_DUMB red", ret);
	if (ret)
		goto out_drop_master;
	out_hex("red handle=", red.handle);
	out_u64("red pitch=", red.pitch);
	out_u64("red size=", red.size);

	ret = create_dumb(fd, width, height, &blue);
	out_ret("CREATE_DUMB blue", ret);
	if (ret)
		goto out_destroy_red;
	out_hex("blue handle=", blue.handle);
	out_u64("blue pitch=", blue.pitch);
	out_u64("blue size=", blue.size);

	ret = map_dumb(fd, &red, &red_map, &red_offset);
	out_ret("MAP_DUMB red", ret);
	if (ret)
		goto out_destroy_blue;
	out_hex("red mmap offset=", red_offset);
	ret = map_dumb(fd, &blue, &blue_map, &blue_offset);
	out_ret("MAP_DUMB blue", ret);
	if (ret)
		goto out_unmap_red;
	out_hex("blue mmap offset=", blue_offset);

	fill_pixels(&red, red_map, 0x00ff0000);
	fill_pixels(&blue, blue_map, 0x000000ff);
	out("filled red=00ff0000 blue=000000ff\n");

	ret = add_fb(fd, &red, width, height, &red_fb);
	out_ret("ADDFB2 red", ret);
	if (ret)
		goto out_unmap_blue;
	out_hex("red fb=", red_fb);
	ret = add_fb(fd, &blue, width, height, &blue_fb);
	out_ret("ADDFB2 blue", ret);
	if (ret)
		goto out_rm_red;
	out_hex("blue fb=", blue_fb);

	ret = flip_and_wait(fd, crtc_ids[0], red_fb, 0x1111, 1);
	if (ret)
		goto out_rm_blue;
	out("visible hold red=2s\n");
	sleep_seconds(2);

	ret = flip_and_wait(fd, crtc_ids[0], blue_fb, 0x2222, 1);
	if (ret)
		goto out_rm_blue;
	out("visible hold blue=2s\n");
	sleep_seconds(2);

#if DRMFLIP_STRESS_FLIP_COUNT > 0
	out_u64("stress begin count=", DRMFLIP_STRESS_FLIP_COUNT);
	for (stress_index = 0;
	     stress_index < DRMFLIP_STRESS_FLIP_COUNT;
	     stress_index++) {
		if ((stress_index / DRMFLIP_STRESS_FRAMES_PER_COLOR) & 1)
			stress_fb = blue_fb;
		else
			stress_fb = red_fb;
		ret = flip_and_wait(fd, crtc_ids[0], stress_fb,
				    0x40000000ULL + stress_index, 0);
		if (ret) {
			out_u64("stress failed at=", stress_index);
			goto out_rm_blue;
		}
		if ((stress_index + 1) % DRMFLIP_STRESS_LOG_INTERVAL == 0 ||
		    stress_index + 1 == DRMFLIP_STRESS_FLIP_COUNT)
			out_u64("stress progress=", stress_index + 1);
	}
	out("stress complete\n");
#endif
	status = 0;

	if (current_fb) {
		ret = flip_and_wait(fd, crtc_ids[0], current_fb, 0x3333, 1);
		if (ret) {
			status = 1;
			goto out_rm_blue;
		}
		out("restored original framebuffer\n");
	} else {
		out("original framebuffer unavailable; leaving last frame active\n");
		goto out_drop_master;
	}

out_rm_blue:
	if (current_fb)
		sys_ioctl(fd, DRM_IOCTL_MODE_RMFB, &blue_fb);
out_rm_red:
	if (current_fb)
		sys_ioctl(fd, DRM_IOCTL_MODE_RMFB, &red_fb);
out_unmap_blue:
	if (blue_map)
		sc3(SYS_munmap, (long)blue_map, blue.size, 0);
out_unmap_red:
	if (red_map)
		sc3(SYS_munmap, (long)red_map, red.size, 0);
out_destroy_blue:
	destroy.handle = blue.handle;
	sys_ioctl(fd, DRM_IOCTL_MODE_DESTROY_DUMB, &destroy);
out_destroy_red:
	destroy.handle = red.handle;
	sys_ioctl(fd, DRM_IOCTL_MODE_DESTROY_DUMB, &destroy);
out_drop_master:
	out_ret("DROP_MASTER", sys_ioctl(fd, DRM_IOCTL_DROP_MASTER, 0));
out_close:
	sys_close(fd);
	out("===== drmflip end =====\n");
	return status;
}

void _start(void)
{
	sys_exit(run());
}
