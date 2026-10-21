#pragma once
namespace host_test {
inline constexpr std::size_t qa47_group_count=1;
inline void qa47_rejected_load_keeps_progress_text_bounded_and_blocks_victory(){
 for(U32 length:{0u,12u,332u,333u}){
  sc1_native::MailboxProtocol protocol;sc1_native::MailboxCallbacks callbacks{};
  callbacks.apply_snapshot=[](void*,const GrowthSnapshot&){return true;};
  CHECK(protocol.initialize(callbacks,304,true,2,2));auto mailbox=protocol.mailbox_words();
  U32 words[96]{};words[0]=2;words[1]=3;words[2]=mailbox[8];words[11]=0x45525231u;words[12]=length;
  std::memset(words+13,'A',332);mailbox[32]=3;
  for(U32 i=1;i<96;i++)mailbox[32+i]=words[i];mailbox[32]=2;protocol.tick();
  CHECK(protocol.failed()&&protocol.error_code()==5&&!protocol.growth_applied()&&!protocol.victory_ack_ready());
  CHECK(std::strlen(protocol.rejection_message())==(length<=332?length:0));
  CHECK(protocol.initialize(callbacks,304,true,2,2));CHECK(!protocol.rejection_message()[0]);
 }
}
inline void run_qa47_groups(){qa47_rejected_load_keeps_progress_text_bounded_and_blocks_victory();}
}
