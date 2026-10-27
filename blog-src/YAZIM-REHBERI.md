# Uslu blog yazım rehberi

Bu klasördeki her `.md` dosyası usluapp.co/blog altında bir makale olur (`build_blog.py` HTML'e çevirir).
Hedef okuyucu: Türkiye'de köpeğiyle yaşayan, Google'a ya da bir yapay zekâ asistanına sorununu soran kişi.
Hedef: aramada üst sıralara çıkan, yapay zekâ botlarının alıntılayabileceği, güvenilir ve sıcak Türkçe makaleler.

## Dosya biçimi

```
---
slug: yavru-kopek-tuvalet-egitimi
title: Yavru köpek tuvalet eğitimi nasıl verilir?
seo_title: Yavru Köpek Tuvalet Eğitimi: Adım Adım Ödüllü Yöntem
description: 140-155 karakter, anahtar kelimeyi içeren, tıklatan özet.
keyword: yavru köpek tuvalet eğitimi
keywords: [yavru köpek çiş eğitimi, yavru köpek tuvalet alıştırma, ...]   # 4-6 ilgili arama
category: tuvalet        # temel | tuvalet | davranis | yavru | bilim | yasam
course: Yavru tuvalet planı   # uygulamadaki ilgili kursun adı (KONULAR.md'de verildi)
date: 2026-10-27
summary: 2-3 cümlelik kısa cevap. Bir yapay zekâ "kısaca" diye özetlese ne derdi? Doğrudan cevap ver.
faq:
  - q: Soru (insanların Google'a yazdığı biçimde)
    a: 2-4 cümlelik net cevap.
  (3 ile 5 soru)
sources:
  - Ziv G. (2017). The effects of using aversive training methods in dogs, a review. Journal of Veterinary Behavior, 19, 50-60. https://doi.org/10.1016/j.jveb.2017.02.004
  (3 ile 6 kaynak)
---

Makale gövdesi (Markdown)
```

## Gövde

- **1100 ile 1600 kelime.** Kısa paragraflar (2 ile 4 cümle). Mobilde okunacak.
- Yapı:
  1. Giriş: okurun yaşadığı durumla başla (2 ile 3 paragraf). İlk 100 kelimede anahtar kelime geçsin.
  2. `## Neden böyle yapıyor?` gibi sebebi anlatan bölüm.
  3. `## Adım adım ...` bölümü: numaralı liste, her adım somut (süre, yer, kaç tekrar).
  4. `## Bilim ne diyor?` bölümü: araştırmaları yazar ve yıl ile anlat ("Vieira de Castro ve arkadaşlarının 2020'de Portekiz'de yaptığı çalışmada..."). Ne bulunduğunu gündelik dille söyle, abartma, çalışmanın sınırını gerekiyorsa belirt.
  5. `## Sık yapılan hatalar` (madde listesi, 3 ile 5 madde).
  6. Gerekiyorsa `## Ne zaman uzmana başvurmalı?` (saldırganlık, ani davranış değişikliği, ağrı belirtisi, kaynak koruma, ağır kaygı).
  7. Kısa bir kapanış.
- H2 başlıkları soru ya da açık ifade olsun; bazıları insanların arattığı soruyla aynı olsun (öne çıkan snippet ve yapay zekâ cevapları için).
- En az bir **numaralı liste** ve bir **madde listesi** olsun. Gerekirse küçük bir Markdown tablosu kullan (ör. yaşa göre tuvalet aralığı).
- **İç linkler:** gövdede 2 ile 4 başka makaleye link ver: `[metin](/blog/diger-slug/)`. Slug'ları KONULAR.md'den al.
- Uslu'dan gövdede **en fazla bir kez**, doğal biçimde bahset ("Uslu'daki Yavru tuvalet planı kursu bu adımları günlük görevlere böler."). Reklam dili yok. Uygulama indirme kutularını şablon kendisi ekler.

## Dil ve üslup

- `uslu/icerik/USLUP.md` dosyasındaki **ton ve anlatım (21-26)**, **sektör dili (14-20)** ve **kelime tablosu** kurallarına uy. "Sen" diliyle, sıcak, yargısız; bir eğitmenin köpek sahibine anlattığı gibi.
- Blogda iki nokta üst üste ve normal noktalama serbest; ama uzun çizgi (—) kullanma, onun yerine nokta ya da virgül kullan.
- **"Kaza" kelimesini kullanma.** Evde tuvalet için "eve tuvalet yapmak", "evde çiş" de.
- Kayış (gezdirirken tutulan ip), tasma (boyna takılan), göğüs tasması. "Gevşek tasma" değil "kayışı çekmeden yürüme".
- Türkiye'den örnekler: apartman, asansör, mahalle, park, misafir, kapı zili, sokak köpekleri, havai fişek (düğün, maç, yılbaşı).
- Kesin söz verme: "genellikle", "çoğu köpekte", "zamanla".
- Yalnızca **ödüle dayalı** yöntemler öner. Ceza, bağırma, burnunu sürtme, sprey, şok tasması, boğma tasması önerme; gerekiyorsa neden zararlı olduğunu açıkla.
- **İlaç, doz, teşhis verme.** Sağlıkla ilgili kısımlarda "veteriner hekiminize danışın" de (genel uyarılarda "siz" dili).
- İngilizce terim gerekiyorsa bir kez parantez içinde ver: "çağırınca gelme (recall)".
- Emoji yok. Özgün metin yaz; başka sitelerden cümle kopyalama.

## Kaynaklar

- Kaynakları **yalnızca** `uslu/arastirma/01-egitim-bilimi.md`, `02-davranis-sorunlari-refah.md`, `03-mufredat-standartlari-ve-urun.md` dosyalarındaki kaynakça tablolarından al. Künyeyi ve DOI/URL'yi oradan aynen kopyala. Uydurma kaynak ya da DOI yazma.
- Gövdede andığın her çalışma `sources` listesinde olsun.
- Rapordaki bulguyu rapordaki kadar güçlü anlat; "kanıtlandı" deme, "gösterdi", "işaret ediyor" de.
- Uygulamadaki ilgili ders içerikleri `uslu/icerik/kurslar/<kategori>/*.json` dosyalarında; adımlar ve örnekler için oradan yararlan ama metni blog için baştan yaz.
