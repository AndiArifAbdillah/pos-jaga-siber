# Naskah rekaman suara: video Pos Jaga Siber

Ada 41 kalimat, sekitar 5–6 menit kalau dibaca. Nomor kalimat **tidak** ikut dibaca.

## Cara merekam

1. Cari kamar yang sunyi dan banyak kain (kasur, lemari baju, gorden). Matikan kipas dan AC. Aktifkan mode pesawat.
2. Pegang HP sekitar 15–20 cm dari mulut, agak menyamping supaya bunyi "p" dan "b" tidak meletup. Rekam sambil berdiri.
3. Rekam dengan aplikasi perekam suara bawaan HP. Boleh satu rekaman panjang, boleh juga satu rekaman per adegan.
4. **Diam sekitar 2 detik di antara kalimat.** Tarik napas dan hitung "satu, dua" dalam hati.
5. **Kalau salah, diam 2 detik, lalu ulangi kalimat itu dari awal.** Tidak perlu menghentikan rekaman. Yang dipakai adalah ulangan terakhir.
6. Baca seperti bercerita ke teman, bukan membaca teks. Senyum saat bicara: senyum terdengar di suara. Ikuti arahan di setiap adegan.
7. "AI" dibaca **ei-ai**. Istilah Inggris (machine learning, Isolation Forest, dashboard) dibaca biasa dalam bahasa Inggris.

Waktu animasi di video akan mengikuti kecepatan bicaramu, jadi tidak perlu terburu-buru dan tidak perlu menonton videonya saat merekam.

## Adegan 1: Pembuka

*Arahan: Pelan dan tegang, seperti membuka cerita. Diam sebentar sebelum 'Inilah Pos Jaga Siber', lalu ucapkan dengan mantap.*

1. Pukul dua pagi di sebuah markas. Listrik PLN padam, dan genset seharusnya menyala.
2. Tapi seseorang di jaringan kantor baru saja mengirim perintah untuk mematikannya.
3. Tidak ada antivirus yang menjaga genset. Dan petugas jaga bukan ahli siber.
4. Inilah Pos Jaga Siber.

## Adegan 2: Masalah

*Arahan: Serius, seperti menjelaskan masalah nyata. Kalimat terakhir adalah pertanyaan: naikkan nada di ujungnya.*

5. Markas hari ini punya dua jaringan: komputer kantor, dan peralatan seperti genset, kamera CCTV, dan kunci pintu elektronik.
6. Peralatan ini tidak bisa dipasangi antivirus, jarang diperbarui, dan bahasanya tidak memakai kata sandi.
7. Serangan seperti ini sudah terjadi, dari jaringan listrik Ukraina tahun dua ribu lima belas, sampai ratusan ribu kamera yang diambil alih.
8. Lalu siapa yang menjaga, kalau penjaganya bukan ahli, dan internetnya bisa putus kapan saja?

## Adegan 3: Cara kerja

*Arahan: Lebih cerah dan yakin, karena ini jawabannya. Tekan kata 'langsung memutus' dan 'tidak bisa diubah diam-diam'.*

9. Pos Jaga Siber adalah kotak penjaga di markas. Ia menerima salinan lalu lintas jaringan, tanpa mengganggu jaringan itu sendiri.
10. Serangan yang sudah dikenal ditangkap aturan Suricata. Yang belum dikenal, ditangkap AI yang mempelajari kebiasaan normal.
11. Kalau ancamannya kritis dan menyangkut peralatan, kotak langsung memutus pelakunya lewat router MikroTik.
12. Setiap kejadian dijelaskan AI lokal dalam bahasa sehari-hari, lalu dicatat di catatan bukti yang tidak bisa diubah diam-diam.
13. Semuanya berjalan di dalam kotak: tetap menjaga meskipun internet putus, dan data markas tidak keluar.

## Adegan 4: Cara kerja: Suricata

*Arahan: Santai, seperti menjelaskan ke teman. Tekan kata 'cocok' dan 'belum dikenal'.*

14. Lalu, apa itu Suricata? Suricata adalah program pendeteksi serangan jaringan yang gratis dan terbuka, dikembangkan yayasan O-I-S-F, dan dipakai luas di banyak negara.
15. Cara kerjanya seperti petugas pemeriksa di pos gerbang: setiap paket data yang lewat dibuka, lalu dicocokkan dengan buku aturan berisi ciri-ciri serangan.
16. Kalau ada yang cocok, Suricata menulis catatan. Catatan itulah yang dibaca kotak kami untuk memutuskan, memblokir, dan menjelaskan ke petugas.
17. Tapi Suricata hanya mengenali serangan yang sudah ada aturannya. Karena itu kami menambahkan AI untuk menangkap yang belum dikenal.

## Adegan 5: Ancamannya nyata

*Arahan: Pelan. Tekan 'tanpa kata sandi apa pun' dan 'mematikannya'.*

18. Di lab kami, genset tiruan memakai bahasa Modbus yang sama dengan panel genset sungguhan.
19. Satu perintah dari jaringan, tanpa kata sandi apa pun, sudah cukup untuk mematikannya.

## Adegan 6: Demo: serangan ke genset

*Arahan: Sedikit lebih cepat dan bersemangat, seperti melaporkan kejadian yang sedang berlangsung. Tekan 'langsung' dan 'otomatis'.*

20. Berikut rekaman dashboard aslinya, berjalan di laptop dengan contoh catatan sensor.
21. Sebuah laptop asing muncul di jaringan kantor, lalu mengirim perintah tulis ke genset utama.
22. Kejadian ini langsung ditandai kritis, dan laptop itu diisolasi otomatis tanpa menunggu petugas.
23. AI lokal menjelaskan apa yang terjadi, kenapa berbahaya, dan langkah SOP yang bisa dicentang petugas.

## Adegan 7: Petugas yang memutuskan

*Arahan: Tenang dan jelas. Tekan 'keputusan tetap di tangan petugas'.*

24. Tidak semua kejadian diblokir otomatis. Kamera gerbang yang mengunggah empat puluh delapan megabita ke luar markas, ditandai tinggi.
25. Laptop staf yang menghubungi alamat luar dengan jarak waktu sangat teratur, ciri program jahat yang melapor ke pengendalinya, juga ditandai.
26. Untuk kejadian seperti ini, keputusan tetap di tangan petugas, cukup dengan satu tombol.

## Adegan 8: AI deteksi perilaku

*Arahan: Bangun rasa penasaran di kalimat pertama, lalu jelaskan prinsipnya pelan-pelan. 'Machine learning' dan 'Isolation Forest' dibaca biasa dalam bahasa Inggris.*

27. Sekarang, serangan yang tidak punya aturan sama sekali. Kunci pintu gudang senjata tiba-tiba menghubungi empat belas perangkat, dalam sepuluh detik.
28. Di sinilah AI deteksi perilaku bekerja. Kotak mempelajari kebiasaan normal setiap jaringan, dengan machine learning bernama Isolation Forest.
29. Prinsipnya sederhana: yang aneh lebih cepat terpisah dari kerumunan. Perangkat normal butuh banyak belahan, perangkat aneh cukup dua atau tiga.
30. Hasilnya, skor keanehan satu koma nol, lengkap dengan alasannya. Dan seperti semua temuan AI, keputusan tetap di tangan petugas.

## Adegan 9: Asisten piket

*Arahan: Ramah dan ringan.*

31. AI ketiga adalah asisten piket. Petugas cukup bertanya dengan bahasa sehari-hari.
32. Asisten mencari di catatan kotak dulu, lalu menjawab hanya dari data itu, lengkap dengan nomor kejadian sumbernya.
33. Kalau datanya tidak ada, ia mengaku tidak tahu. Dan di akhir piket, laporan ganti piket tersusun dengan satu tombol.

## Adegan 10: Catatan bukti

*Arahan: Serius dan tegas, terutama di 'rantainya putus'.*

34. Setiap kejadian dan tindakan petugas disimpan seperti rantai: setiap entri mengunci sidik jari entri sebelumnya, dan ditandatangani kotak.
35. Kalau satu entri saja dihapus untuk menghilangkan jejak, rantainya putus, dan kotak langsung menunjukkan entri mana yang hilang.
36. Kode pendek di layar disalin ke buku jaga kertas setiap ganti piket, menjadi saksi yang tidak bisa dihapus dari jauh.

## Adegan 11: Prinsip

*Arahan: Tegas dan meyakinkan. Beri tekanan pada 'Tidak ada AI yang bisa memblokir'.*

37. Prinsip kami: AI menemukan dan menjelaskan, sedangkan aturan tetap dan manusia yang memutuskan. Tidak ada AI yang bisa memblokir.
38. Blokir otomatis hanya untuk kejadian kritis pada peralatan, berlaku dua puluh empat jam, dan tidak pernah menyentuh router atau kotak itu sendiri.

## Adegan 12: Siap dipasang

*Arahan: Bangga dan mantap. Kalimat terakhir diucapkan pelan, frasa demi frasa.*

39. Perangkat lunaknya bebas biaya lisensi. Kotaknya cukup satu mini PC dengan dua colokan jaringan, ditambah router MikroTik yang umumnya sudah ada di markas.
40. Purwarupa ini lulus empat puluh satu tes otomatis, dan seluruh kode serta dokumentasinya terbuka untuk dewan juri.
41. Pos Jaga Siber. Penjaga jaringan markas yang bekerja mandiri, menjelaskan ancaman dalam bahasa sehari-hari, dan langsung mengamankan peralatan penting.
