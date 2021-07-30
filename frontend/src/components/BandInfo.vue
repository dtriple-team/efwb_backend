<template>
  <div>
    <v-card flat height="120" class="primary rounded-0 mx-auto"> </v-card>
    <v-card
      flat
      width="100"
      height="100"
      class="center secondary mt-n13 mx-auto"
      ><v-icon size="85" color="black" class="icon">
        mdi-account-circle
      </v-icon>
    </v-card>
    <v-card flat>
      <v-card-text class="display-1 text-center font-weight-bold">
        {{ band.name }}
      </v-card-text>
    </v-card>
    <v-container fluid>
      <v-list>
        <div class="border-style-top rounded-t-lg">
          <v-list-item-title class="title-style-margin"
            >생체 데이터</v-list-item-title
          >
          <v-list-item>
            <v-list-item-content v-for="(item, i) in banddata.vital" :key="i">
              <div class="mx-auto text-center">
                <v-avatar color="thirdly" size="90" class="mb-2">
                  <span class="text-h5 font-weight-bold">{{ item.value }}</span>
                </v-avatar>
                <v-list-item-title class="title-style">{{
                  item.title
                }}</v-list-item-title>
              </div>
            </v-list-item-content>
          </v-list-item>
        </div>
        <div flat outlined class="border-style rounded-b-lg">
          <v-list-item-title class="title-style-margin"
            >밴드 상태</v-list-item-title
          >
          <v-list-item>
            <v-list-item-content>
              <div class="mx-auto text-center">
                <v-avatar color="thirdly" size="55" class="mb-2">
                  <v-icon color="black">
                    mdi-check-bold
                  </v-icon>
                </v-avatar>
                <v-list-item-title class="title-style">착용</v-list-item-title>
              </div>
            </v-list-item-content>
            <v-list-item-content>
              <div class="mx-auto text-center">
                <v-avatar color="thirdly" size="55" class="mb-2">
                  <span class="text-h5 font-weight-bold">80</span>
                </v-avatar>
                <v-list-item-title class="title-style"
                  >수신감도</v-list-item-title
                >
              </div>
            </v-list-item-content>
            <v-list-item-content>
              <div class="mx-auto text-center">
                <v-avatar color="thirdly" size="55" class="mb-2">
                  <span class="text-h5 font-weight-bold">80</span>
                </v-avatar>
                <v-list-item-title class="title-style"
                  >배터리</v-list-item-title
                >
              </div>
            </v-list-item-content>
            <v-list-item-content>
              <div class="mx-auto text-center">
                <v-avatar color="thirdly" size="55" class="mb-2">
                  <v-icon color="black">mdi-walk</v-icon>
                </v-avatar>
                <v-list-item-title class="title-style">활동</v-list-item-title>
              </div>
            </v-list-item-content>
          </v-list-item>
        </div>
        <div flat class="border-style rounded-lg mt-5">
          <v-list-item-title class="title-style-margin"
            >활동 이력</v-list-item-title
          >
          <v-list-item>
            <v-list-item-content v-for="(item, i) in banddata.active" :key="i">
              <div class="mx-auto text-center">
                <v-avatar color="thirdly" size="55" class="mb-2">
                  <span class="text-h5 font-weight-bold">{{ item.value }}</span>
                </v-avatar>
                <v-list-item-title class="title-style">{{
                  item.title
                }}</v-list-item-title>
              </div>
            </v-list-item-content>
          </v-list-item>
        </div>
      </v-list>
      <v-list class="border-style rounded-lg mt-1">
        <div outlined class="border-style-top rounded-t-lg">
          <v-list-item-title class="title-style-margin"
            >밴드 정보</v-list-item-title
          >
          <v-list-item>
            <v-list-item-icon>
              <v-icon>
                mdi-watch-variant
              </v-icon>
            </v-list-item-icon>
            <v-list-item-content>
              {{ userdata.bandinfo }}
            </v-list-item-content>
          </v-list-item>
        </div>
        <div class="border-style-top rounded-0">
          <v-list-item-title class="title-style-margin"
            >개인 정보</v-list-item-title
          >
          <v-list-item v-for="(item, i) in userdata.personalinfo" :key="i">
            <v-list-item-icon>
              <v-icon>
                {{ item.icon }}
              </v-icon>
            </v-list-item-icon>
            <v-list-item-content>
              {{ item.value }}
            </v-list-item-content>
          </v-list-item>
        </div>
        <div class="border-style rounded-b-lg">
          <v-list-item-title class="title-style-margin"
            >담당자</v-list-item-title
          >
          <v-list-item v-for="(item, i) in userdata.managerinfo" :key="i">
            <v-list-item-icon>
              <v-icon>
                mdi-account-tie
              </v-icon>
            </v-list-item-icon>
            <v-list-item-content>
              {{ item.value }}
            </v-list-item-content>
            <v-list-item-action>
              <v-list-item-title>{{ item.position }}</v-list-item-title>
            </v-list-item-action>
          </v-list-item>
        </div>
      </v-list>
    </v-container>
  </div>
</template>

<script>
export default {
  props: {
    bandInfo: {
      type: String,
      default: "",
    },
  },
  data: () => ({
    band: "",
    banddata: {
      vital: [
        {
          value: 80,
          title: "심박수 (BPM)",
        },
        {
          value: 80,
          title: "산소포화도 (%)",
        },
      ],
      bandstate: [
        {
          value: 3,
          title: "착용",
        },
        {
          value: -43,
          title: "수신감도",
        },
        {
          value: 80,
          title: "배터리",
        },
        {
          value: 3,
          title: "활동",
        },
      ],
      active: [
        {
          value: 80,
          title: "걷기",
        },
        {
          value: 80,
          title: "달리기",
        },
        {
          value: 80,
          title: "칼로리",
        },
        {
          value: 1,
          title: "낙상",
        },
      ],
    },
    userdata: {
      bandinfo: "0x00",
      personalinfo: [
        {
          icon: "mdi-card-account-details",
          value: "김갑생",
        },
        {
          icon: "mdi-calendar-today",
          value: "1947년 09월 1일",
        },
      ],
      managerinfo: [
        {
          value: "하재경",
          position: "staff",
        },
        {
          value: "김갑슨",
          position: "manager",
        },
      ],
    },
  }),
  mounted() {
    this.changeJson();
  },
  created() {
    // this.check();
  },
  methods: {
    changeJson() {
      this.band = JSON.parse(this.bandInfo);
    },
    changeIcon(data, check) {
      if (check) {
        switch (data) {
          case 3:
            return "mdi-check-bold";
        }
      } else {
        switch (data) {
          case 2:
            return "mdi-walk";
          case 3:
            return "mdi-run";
          case 4:
            return "mdi-bike";
        }
      }
    },
  },
};
</script>
<style lang="scss">
.border-style {
  border: 1px solid #d3d3d3;
}
.border-style-top {
  border-left: 1px solid #d3d3d3;
  border-right: 1px solid #d3d3d3;
  border-top: 1px solid #d3d3d3;
}
.border-style-bottom {
  border-left: 1px solid #d3d3d3;
  border-right: 1px solid #d3d3d3;
  border-bottom: 1px solid #d3d3d3;
}

.center {
  position: relative;
}
.icon {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}
.title-style {
  font-size: 0.875rem;
  color: black;
}
.title-style-margin {
  font-size: 0.875rem;
  color: black;
  margin-left: 8px;
  margin-top: 8px;
}
</style>
