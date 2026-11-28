(() => {
  const audio = document.getElementById('spotify-audio');
  if (!audio) return;
  const $ = (id) => document.getElementById(id);
  const csrf = () => document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1] || document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
  let currentSongId = $('player-like')?.dataset.songId || null;
  let shuffle = false;
  let repeatMode = 'off'; // off | all | one
  let queue = [];
  let navigationBusy = false;

  async function postJSON(url, body) {
    const response = await fetch(url, {method:'POST', headers:{'Content-Type':'application/json','X-CSRFToken':csrf(),'X-Requested-With':'XMLHttpRequest'}, body:JSON.stringify(body)});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Request failed');
    return data;
  }
  function setStatus(message) { const el=$('player-status'); if(el) el.textContent=message; }
  function updateSong(song, autoplay=true) {
    if (!song) return;
    currentSongId = String(song.id);
    const cover=$('player-cover');
    if (cover) { cover.src=song.cover_url; cover.alt=song.title; }
    else {
      const img=document.createElement('img'); img.id='player-cover'; img.className='player-thumb'; img.src=song.cover_url; img.alt=song.title;
      $('player-track-info').prepend(img);
    }
    $('player-title').textContent=song.title;
    const artist=$('player-artist'); artist.textContent=song.artist; artist.href=song.artist_url;
    let like=$('player-like');
    if (!like) { like=document.createElement('button'); like.type='button'; like.id='player-like'; like.className='heart-btn'; like.textContent='♥'; like.title='Save to Liked Songs'; $('player-track-info').append(like); }
    like.dataset.songId=song.id;
    like.classList.toggle('liked', document.querySelector(`.heart-btn[data-song-id="${song.id}"].liked`) !== null);
    if (audio.src !== new URL(song.audio_url, location.href).href) audio.src=song.audio_url;
    if (autoplay && song.audio_url) audio.play().then(()=>{$('play-pause-btn').textContent='Ⅱ';setStatus('Now playing');}).catch(()=>setStatus('Press play to start audio'));
    else setStatus(song.audio_url ? 'Ready to play' : 'Audio file is not available for this song');
  }
  function collectQueue(clickedLink) {
    const ids=[...document.querySelectorAll('a[href*="play="]')].map(a=>new URL(a.href,location.href).searchParams.get('play')).filter(Boolean);
    const unique=[...new Set(ids)];
    const selected=new URL(clickedLink.href,location.href).searchParams.get('play');
    if(selected && !unique.includes(selected)) unique.unshift(selected);
    return unique.map(Number);
  }
  async function playSong(songId, ids) {
    try {
      setStatus('Loading…');
      const data=await postJSON('/api/player/play/',{song_id:Number(songId),queue:ids?.length?ids:[Number(songId)]});
      queue=data.queue || [];
      updateSong(data.song,true);
      const url=new URL(location.href); url.searchParams.delete('play'); history.replaceState({},'',url);
    } catch(error) { setStatus(error.message); }
  }
  async function step(action) {
    try {
      const data=await postJSON('/api/player/step/',{action,shuffle,repeat_all:repeatMode==='all'});
      if(data.ended){setStatus('Queue finished');$('play-pause-btn').textContent='▶';return;}
      queue=data.queue || queue; updateSong(data.song,true);
    } catch(error){setStatus(error.message);}
  }
  $('play-pause-btn')?.addEventListener('click',()=>{
    if(!audio.src){setStatus('Choose a song first');return;}
    if(audio.paused) audio.play().then(()=>{$('play-pause-btn').textContent='Ⅱ';}).catch(()=>setStatus('Unable to play this audio file'));
    else {audio.pause();$('play-pause-btn').textContent='▶';}
  });
  $('next-btn')?.addEventListener('click',()=>step('next'));
  $('previous-btn')?.addEventListener('click',()=>{if(audio.currentTime>3){audio.currentTime=0;return;}step('previous');});
  $('shuffle-btn')?.addEventListener('click',()=>{shuffle=!shuffle;$('shuffle-btn').classList.toggle('is-active',shuffle);$('shuffle-btn').setAttribute('aria-pressed',String(shuffle));setStatus(shuffle?'Shuffle on':'Shuffle off');});
  $('repeat-btn')?.addEventListener('click',()=>{repeatMode=repeatMode==='off'?'all':repeatMode==='all'?'one':'off';const b=$('repeat-btn');b.dataset.mode=repeatMode;b.classList.toggle('is-active',repeatMode!=='off');b.title='Repeat: '+repeatMode;b.textContent=repeatMode==='one'?'↻¹':'↻';setStatus('Repeat '+repeatMode);});
  audio.addEventListener('play',()=>$('play-pause-btn').textContent='Ⅱ');
  audio.addEventListener('pause',()=>$('play-pause-btn').textContent='▶');
  audio.addEventListener('ended',()=>{if(repeatMode==='one'){audio.currentTime=0;audio.play();}else step('next');});

  // Song links: update the queue and audio without navigating/reloading.
  document.addEventListener('click',event=>{
    const link=event.target.closest('a[href*="play="]');
    if(!link || event.defaultPrevented || event.button!==0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const id=new URL(link.href,location.href).searchParams.get('play'); if(!id)return;
    event.preventDefault(); playSong(id,collectQueue(link));
  });

  // Like buttons/links work asynchronously and preserve the current audio stream.
  document.addEventListener('click',async event=>{
    const link=event.target.closest('a.heart-btn');
    const playerButton=event.target.closest('#player-like');
    const target=playerButton || link;
    if(!target)return;
    const match=(target.href||'').match(/\/song\/(\d+)\/like\//);
    const id=target.dataset.songId || match?.[1]; if(!id)return;
    event.preventDefault();
    try {
      const response=await fetch(`/api/song/${id}/like/`,{method:'POST',headers:{'X-CSRFToken':csrf(),'X-Requested-With':'XMLHttpRequest'}});
      if(response.status===403 || response.redirected){location.href=response.url || '/login/';return;}
      const data=await response.json();
      document.querySelectorAll(`.heart-btn[href*="/song/${id}/like/"], .heart-btn[data-song-id="${id}"]`).forEach(btn=>btn.classList.toggle('liked',data.liked));
      if(currentSongId===String(id)) target.classList.toggle('liked',data.liked);
      setStatus(data.liked?'Added to Liked Songs':'Removed from Liked Songs');
    }catch(error){setStatus('Could not update liked songs');}
  });

  // Playlist-add forms submit in the background; other normal forms remain unchanged.
  document.addEventListener('submit',async event=>{
    const form=event.target;
    const match=(form.action||'').match(/\/song\/(\d+)\/add-to-playlist\//);
    if(!match)return;
    event.preventDefault();
    try {
      const response=await fetch(`/api/song/${match[1]}/add-to-playlist/`,{method:'POST',headers:{'X-CSRFToken':csrf(),'X-Requested-With':'XMLHttpRequest'},body:new FormData(form)});
      if(response.status===403 || response.redirected){location.href=response.url || '/login/';return;}
      const data=await response.json(); setStatus(data.success?`Added to ${data.playlist}`:'Could not add to playlist');
    }catch(error){setStatus('Could not add to playlist');}
  });

  // Fetch-based page navigation swaps only the main content; the audio element is never replaced.
  async function navigate(url, push=true) {
    if(navigationBusy)return; navigationBusy=true;
    try {
      const response=await fetch(url,{headers:{'X-Requested-With':'XMLHttpRequest'}});
      if(!response.ok) throw new Error('Navigation failed');
      const html=await response.text(); const doc=new DOMParser().parseFromString(html,'text/html');
      const incoming=doc.querySelector('.main-view'); const current=document.querySelector('.main-view');
      if(!incoming||!current) {location.href=url;return;}
      current.innerHTML=incoming.innerHTML;
      document.title=doc.title;
      if(push)history.pushState({},'',url);
      window.scrollTo(0,0);
    } catch(error){location.href=url;} finally {navigationBusy=false;}
  }
  document.addEventListener('click',event=>{
    const link=event.target.closest('a[href]');
    if(!link || event.defaultPrevented || event.button!==0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    if(link.target==='_blank' || link.hasAttribute('download') || link.getAttribute('href').startsWith('#'))return;
    const url=new URL(link.href,location.href);
    if(url.origin!==location.origin || url.pathname.startsWith('/admin/') || url.pathname==='/logout/')return;
    if(url.searchParams.has('play'))return;
    event.preventDefault(); navigate(url.href,true);
  });
  document.addEventListener('submit',event=>{
    const form=event.target;
    if(form.matches('.topbar-search')){event.preventDefault();const url=new URL(form.action,location.href);new FormData(form).forEach((v,k)=>url.searchParams.set(k,v));navigate(url.href,true);}
  });
  window.addEventListener('popstate',()=>navigate(location.href,false));
})();
